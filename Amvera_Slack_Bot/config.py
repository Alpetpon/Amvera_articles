import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токен Slack бота
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Проверочный токен для Slack
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# API-ключ для OpenWeatherMap
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
