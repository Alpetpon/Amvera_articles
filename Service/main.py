import requests
import time
import psycopg2
from datetime import datetime

AMOCRM_DOMAIN = 'AMODOMAIN.amocrm.ru'
ACCESS_TOKEN = 'TOKEN'
TELEGRAM_BOT_TOKEN = 'BOT_TOKEN'


DB_CONFIG = {
    'dbname': 'DBNAME',
    'user': 'NAME',
    'password': 'PASSWORD',
    'host': 'HOST',
    'port': 5432
}
UPDATE_OFFSET = None

STAGE_MAPPING = {
    74340914: "Первичный конракт",
    74340918: "Переговоры",
    74340922: "Ожидает подписания",
    74340926: "Заключена"
}

def initialize_database():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id SERIAL PRIMARY KEY,
            deal_id INTEGER UNIQUE,
            name TEXT,
            price NUMERIC,
            created_at TIMESTAMP,
            notified BOOLEAN DEFAULT false
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT UNIQUE,
            role TEXT DEFAULT 'user'
        );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("База данных и таблицы успешно инициализированы.")
    except Exception as e:
        print("Ошибка при инициализации базы данных:", e)


def update_database_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("ALTER TABLE deals ADD COLUMN IF NOT EXISTS stage TEXT;")
        conn.commit()
        cur.close()
        conn.close()
        print("Схема базы данных успешно обновлена.")
    except Exception as e:
        print("Ошибка при обновлении схемы базы данных:", e)


def update_user_role(chat_id, role):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = """
        INSERT INTO users (chat_id, role)
        VALUES (%s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET role = EXCLUDED.role;
        """
        cur.execute(query, (chat_id, role))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Роль пользователя {chat_id} обновлена на {role}.")
    except Exception as e:
        print("Ошибка при обновлении роли пользователя:", e)


def add_user(chat_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = "INSERT INTO users (chat_id) VALUES (%s) ON CONFLICT (chat_id) DO NOTHING;"
        cur.execute(query, (chat_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при добавлении пользователя:", e)


def get_all_users():
    users = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT chat_id, role FROM users;")
        rows = cur.fetchall()
        for row in rows:
            users.append({'chat_id': row[0], 'role': row[1]})
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при получении пользователей:", e)
    return users


def update_chat_ids():
    global UPDATE_OFFSET
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {}
    if UPDATE_OFFSET is not None:
        params['offset'] = UPDATE_OFFSET + 1
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        updates = data.get("result", [])
        if updates:
            for update in updates:
                UPDATE_OFFSET = update.get("update_id", UPDATE_OFFSET)
                message = update.get("message", {})
                chat = message.get("chat", {})
                text = message.get("text", "").strip()
                chat_id = chat.get("id")
                if chat_id:
                    if text in ["/start", "/sales", "/admin"]:
                        if text == "/start":
                            role = "user"
                        elif text == "/sales":
                            role = "sales"
                        elif text == "/admin":
                            role = "admin"
                        update_user_role(chat_id, role)
                    else:
                        add_user(chat_id)
    except Exception as e:
        print("Ошибка обновления chat_ids:", e)


def send_message_to_user(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Ошибка отправки сообщения для {chat_id}: {response.text}")
    except Exception as e:
        print(f"Ошибка отправки сообщения для {chat_id}: {e}")


def send_role_based_notification(deal):
    users = get_all_users()
    for user in users:
        role = user['role']
        chat_id = user['chat_id']
        if role == 'admin':
            message = (
                f"[ADMIN] Новая сделка!\n"
                f"ID: {deal['deal_id']}\n"
                f"Название: {deal['name']}\n"
                f"Сумма: {deal['price']} руб.\n"
                f"Стадия: {deal['stage']}\n"
                f"Создана: {deal['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
        elif role == 'sales':
            message = (
                f"[SALES] Новая сделка!\n"
                f"Название: {deal['name']}\n"
                f"Сумма: {deal['price']} руб.\n"
                f"Стадия: {deal['stage']}"
            )
        else:
            message = f"Новая сделка: {deal['name']} (Стадия: {deal['stage']})"
        send_message_to_user(chat_id, message)


def send_status_change_notification(change_info):
    deal = change_info["deal"]
    old_stage = deal["old_stage"]
    new_stage = deal["stage"]
    message = (
        f"Изменение статуса сделки:\n"
        f"Название: {deal['name']}\n"
        f"ID сделки: {deal['deal_id']}\n"
        f"Старый статус: {old_stage}\n"
        f"Новый статус: {new_stage}"
    )
    users = get_all_users()
    for user in users:
        if user["role"] in ["sales", "admin"]:
            send_message_to_user(user["chat_id"], message)


def store_deal_in_db(lead):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        deal_id = lead.get('id')
        name = lead.get('name', 'Нет названия')
        price = lead.get('price', 0)
        created_at_ts = lead.get('created_at', 0)
        created_at = datetime.fromtimestamp(created_at_ts)

        stage_id = lead.get('status_id')
        new_stage = STAGE_MAPPING.get(stage_id, f"Стадия {stage_id}") if stage_id else "Неизвестно"

        cur.execute("SELECT stage FROM deals WHERE deal_id = %s;", (deal_id,))
        result = cur.fetchone()
        if result is None:
            query = """
            INSERT INTO deals (deal_id, name, price, created_at, stage)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (deal_id) DO NOTHING;
            """
            cur.execute(query, (deal_id, name, price, created_at, new_stage))
            conn.commit()
            cur.close()
            conn.close()
            return {"action": "new",
                    "deal": {"deal_id": deal_id, "name": name, "price": price, "created_at": created_at,
                             "stage": new_stage}}
        else:
            old_stage = result[0]
            if old_stage != new_stage:
                cur.execute("UPDATE deals SET stage = %s WHERE deal_id = %s;", (new_stage, deal_id))
                conn.commit()
                cur.close()
                conn.close()
                return {"action": "changed",
                        "deal": {"deal_id": deal_id, "name": name, "price": price, "created_at": created_at,
                                 "stage": new_stage, "old_stage": old_stage}}
            else:
                cur.close()
                conn.close()
                return {"action": "none"}
    except Exception as e:
        print("Ошибка при вставке сделки в БД:", e)
        return {"action": "error"}


def get_unnotified_deals():
    deals = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT deal_id, name, price, created_at, stage FROM deals WHERE notified = false;")
        rows = cur.fetchall()
        for row in rows:
            deals.append({
                'deal_id': row[0],
                'name': row[1],
                'price': row[2],
                'created_at': row[3],
                'stage': row[4]
            })
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при получении неуведомленных сделок:", e)
    return deals


def mark_deal_as_notified(deal_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE deals SET notified = true WHERE deal_id = %s;", (deal_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при обновлении статуса сделки:", e)


def check_new_deals():
    update_chat_ids()
    url = f"https://{AMOCRM_DOMAIN}/api/v4/leads"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка получения данных из amoCRM: {response.status_code} {response.text}")
            return
        data = response.json()
        leads = data.get("_embedded", {}).get("leads", [])
    except Exception as e:
        print("Ошибка запроса к amoCRM:", e)
        return

    status_changes = []
    for lead in leads:
        result = store_deal_in_db(lead)
        if result.get("action") == "changed":
            status_changes.append(result)

    unnotified_deals = get_unnotified_deals()
    for deal in unnotified_deals:
        send_role_based_notification(deal)
        mark_deal_as_notified(deal['deal_id'])

    for change_info in status_changes:
        send_status_change_notification(change_info)


if __name__ == "__main__":
    UPDATE_OFFSET = None
    initialize_database()
    update_database_schema()
    print("Сервис запущен. Ожидание новых сделок и рассылка уведомлений с учетом ролей...")
    while True:
        check_new_deals()
        time.sleep(5)
