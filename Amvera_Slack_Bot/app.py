from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from weather import fetch_weather
from db import init_db, add_task, get_tasks

app = Flask(__name__)

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET

client = WebClient(token=SLACK_BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

init_db()


@app.route('/slack/command', methods=['POST'])
def command_handler():
    data = request.form
    command = data.get('command')
    user_id = data.get('user_id')

    if command == '/hello':
        return hello_command(user_id)
    elif command == '/weather':
        return weather_command(user_id)
    elif command == '/task':
        return task_command(user_id)
    else:
        return jsonify(response_type='ephemeral', text="Команда не поддерживается."), 200


def hello_command(user_id):
    try:
        client.chat_postMessage(
            channel=user_id,
            text="Привет! Как я могу помочь вам сегодня?",
            attachments=[
                {
                    "text": "Выберите опцию:",
                    "fallback": "Выберите опцию",
                    "callback_id": "hello_options",
                    "actions": [
                        {
                            "name": "option",
                            "text": "Получить погоду",
                            "type": "button",
                            "value": "weather"
                        },
                        {
                            "name": "option",
                            "text": "Просмотреть задачи",
                            "type": "button",
                            "value": "tasks"
                        }
                    ]
                }
            ]
        )
        return jsonify(response_type='in_channel', text="Опции отправлены."), 200
    except SlackApiError as e:
        logging.error(f"Ошибка отправки сообщения: {e.response['error']}")
        return jsonify(response_type='ephemeral', text="Произошла ошибка при отправке сообщения."), 500


@app.route('/slack/interactive', methods=['POST'])
def interactive_handler():
    payload = request.json
    actions = payload.get('actions', [])
    action = actions[0] if actions else None
    if action and action['value'] == 'weather':
        return weather_command(payload['user']['id'])
    elif action and action['value'] == 'tasks':
        return task_command(payload['user']['id'])
    else:
        return jsonify(text="Неизвестное действие."), 200


def weather_command(user_id):
    weather_info = fetch_weather()
    try:
        client.chat_postMessage(
            channel=user_id,
            text=weather_info
        )
        return jsonify(response_type='in_channel', text="Прогноз погоды отправлен."), 200
    except SlackApiError as e:
        logging.error(f"Ошибка отправки сообщения: {e.response['error']}")
        return jsonify(response_type='ephemeral', text="Произошла ошибка при отправке сообщения."), 500


def task_command(user_id):
    tasks = get_tasks(user_id)
    if tasks:
        tasks_list = "\n".join([task[0] for task in tasks])
        message = f"Ваши задачи:\n{tasks_list}"
    else:
        message = "У вас нет задач."

    try:
        client.chat_postMessage(
            channel=user_id,
            text=message
        )
        return jsonify(response_type='in_channel', text="Список задач отправлен."), 200
    except SlackApiError as e:
        logging.error(f"Ошибка отправки сообщения: {e.response['error']}")
        return jsonify(response_type='ephemeral', text="Произошла ошибка при отправке сообщения."), 500


# Обработчик событий от Slack
@app.route('/slack/events', methods=['POST'])
def slack_events():
    if 'challenge' in request.json:
        return jsonify({'challenge': request.json['challenge']})

    event = request.json.get('event', {})

    if event.get('type') == 'message' and not event.get('bot_id'):
        user = event.get('user')
        text = event.get('text')
        channel = event.get('channel')

        if 'привет' in text.lower():
            try:
                client.chat_postMessage(
                    channel=channel,
                    text=f"Привет, <@{user}>! Как дела?"
                )
            except SlackApiError as e:
                logging.error(f"Ошибка отправки сообщения: {e.response['error']}")

    return '', 200


if __name__ == "__main__":
    app.run(port=3000)
