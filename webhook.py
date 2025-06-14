from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === Модель для хранения лидов ===
class Lead(db.Model):
    __tablename__ = 'lead'

    id         = db.Column(db.Integer, primary_key=True)
    chat_id    = db.Column(db.String(64), nullable=False)
    fio        = db.Column(db.String(255), nullable=False)
    phone      = db.Column(db.String(50), nullable=False)
    city       = db.Column(db.String(100), nullable=False)
    direction  = db.Column(db.String(255), nullable=False)    # здесь поле direction
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

# === Настройки Wazzup ===
API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID       = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID  = '77766961328'
ADMIN_CHAT_ID    = '77778053727'
WAZZUP_SEND_API  = 'https://api.wazzup24.com/v3/message'

# === Настройки Bitrix24 ===
BITRIX_WEBHOOK_URL = 'https://b24-xq7bnn.bitrix24.kz/rest/1/tnjaxnh7k6xwbyyq/crm.lead.add.json'

CITIES = {
    '1': 'Алматы',    '2': 'Нур-Султан', '3': 'Шымкент',
    '4': 'Караганда','5': 'Актобе',     '6': 'Астана'
}

DIRECTIONS = {
    '1': 'Кирпич и блоки',   '2': 'Цемент и растворы',
    '3': 'Арматура и металлопрокат','4': 'Древесина и пиломатериалы',
    '5': 'Кровельные материалы','6': 'Изоляция и утеплители',
    '7': 'Сантехника и водоснабжение','8': 'Электрооборудование',
    '9': 'Инструменты',       '10': 'Отделочные материалы'
}

RESPONSIBLES = {
    'Алматы': {'name': 'Менеджер Алматы',     'phone': '+7xxx', 'id': 2},
    'Нур-Султан': {'name': 'Менеджер Нур-Султана','phone': '+7xxx', 'id': 3},
    'Шымкент': {'name': 'Менеджер Шымкента',   'phone': '+7xxx', 'id': 4},
    'Караганда': {'name': 'Кирилл Костылев',   'phone': '+77766961328', 'id': 11},
    'Актобе': {'name': 'Менеджер Актобе',      'phone': '+7xxx', 'id': 5},
    'Астана': {'name': 'Менеджер Астаны',      'phone': '+77001234567', 'id': 1},
}

user_states = {}
processed_message_ids = set()

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")

def send_message(chat_id, text):
    headers = {
        'Authorization': f'Bearer {API_BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "channelId": CHANNEL_ID,
        "chatType": "whatsapp",
        "chatId": chat_id,
        "text": text
    }
    try:
        r = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Wazzup ({chat_id}): {r.status_code}")
        return r.status_code in (200, 201)
    except Exception as e:
        log(f"Ошибка отправки в Wazzup: {e}")
        return False

def notify_admin(fio, phone, city, direction):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = (
        f"🔔 *Новая заявка* в Bitrix24\n"
        f"⏰ Время: {now}\n"
        f"👤 Клиент: {fio} ({phone})\n"
        f"🌆 Город: {city}\n"
        f"🎯 Направление: {direction}\n"
        f"✅ Лид ожидает обработки в CRM."
    )
    send_message(ADMIN_CHAT_ID, text)

def create_bitrix_lead(city, direction, fio, phone, chat_id):
    parts = fio.split()
    last   = parts[0] if len(parts) > 0 else ''
    first  = parts[1] if len(parts) > 1 else ''
    second = parts[2] if len(parts) > 2 else ''
    assigned_id = RESPONSIBLES.get(city, {}).get('id', 1)

    comment = (
        f"Источник: WhatsApp Bot\n"
        f"Направление: {direction}\n"
        f"Город: {city}\n"
        f"Телефон клиента: {phone}\n"
        f"Контакт: {fio}"
    )

    # Сохраняем в базу данных
    lead = Lead(chat_id=chat_id, fio=fio, phone=phone, city=city, direction=direction)
    db.session.add(lead)
    db.session.commit()

    data = {
        "fields": {
            "TITLE": f"Optimus KZ Bot: {direction} ({city})",
            "NAME": first, "LAST_NAME": last, "SECOND_NAME": second,
            "ASSIGNED_BY_ID": assigned_id,
            "ADDRESS_CITY": city,
            "COMMENTS": comment,
            "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}],
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    try:
        resp = requests.post(BITRIX_WEBHOOK_URL, json=data, timeout=30)
        log(f"Bitrix: {resp.status_code} / {resp.text}")
        if resp.status_code == 200 and resp.json().get("result"):
            notify_admin(fio, phone, city, direction)
        else:
            send_message(chat_id, "⚠️ Проблема с CRM, менеджер свяжется позже.")
    except Exception as e:
        log(f"Bitrix error: {e}")
        send_message(chat_id, "⚠️ Не удалось соединиться с CRM, попробуйте позже.")

def get_menu_text():
    return "👋 Добро пожаловать в *Optimus KZ*!\n\nВыберите регион:\n" + \
        "\n".join(f"{k}. {v}" for k, v in CITIES.items())

def get_continue_menu():
    return "Спасибо! Чем можем помочь дальше?\n1️⃣ — Подобрать товары\n2️⃣ — Обратный звонок"

def get_directions_menu():
    return "Выберите направление:\n" + \
        "\n".join(f"{k}. {v}" for k, v in DIRECTIONS.items())

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({'status': 'ready'}), 200

    data = request.get_json(force=True)
    log(f"Webhook received: {data}")

    for msg in data.get("messages", []):
        mid     = msg.get("messageId")
        chat_id = msg.get("chatId")
        text    = msg.get("text", "").strip()
        fio     = msg.get("contact", {}).get("name", "Неизвестный")

        # Используем chatId как fallback для телефона
        phone = msg.get("contact", {}).get("phoneNumber") or chat_id

        is_me   = msg.get("fromMe", False)
        is_echo = msg.get("isEcho", False)

        # Фильтрация
        if is_me or is_echo or not text or mid in processed_message_ids or chat_id != ALLOWED_CHAT_ID:
            processed_message_ids.add(mid)
            continue

        processed_message_ids.add(mid)
        state = user_states.get(chat_id, {"step": "city"})

        # Шаг 1: выбор города
        if state["step"] == "city":
            if text in CITIES:
                city = CITIES[text]
                user_states[chat_id] = {"step": "menu", "city": city, "fio": fio, "phone": phone}
                send_message(chat_id, get_continue_menu())
            else:
                send_message(chat_id, get_menu_text())

        # Шаг 2: меню
        elif state["step"] == "menu":
            city = state["city"]
            if text == "1":
                user_states[chat_id]["step"] = "direction"
                send_message(chat_id, get_directions_menu())
            elif text == "2":
                send_message(chat_id, "📞 Ожидайте звонок менеджера в течение 15 минут.")
                create_bitrix_lead(city, "Callback", fio, phone, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_continue_menu())

        # Шаг 3: выбор направления
        elif state["step"] == "direction":
            city = state["city"]
            if text in DIRECTIONS:
                direction = DIRECTIONS[text]
                send_message(chat_id,
                    f"🎯 Вы выбрали: *{direction}* в *{city}*.\nМенеджер свяжется с вами.")
                create_bitrix_lead(city, direction, fio, phone, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_directions_menu())

        # Сброс состояния
        else:
            user_states.pop(chat_id, None)
            send_message(chat_id, get_menu_text())

        # Ограничение размера кеша обработанных сообщений
        if len(processed_message_ids) > 1000:
            processed_message_ids.clear()

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    log("Сервер запущен на порту 10000")
    app.run(host='0.0.0.0', port=10000)
