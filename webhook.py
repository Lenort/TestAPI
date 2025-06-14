from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === Настройки Wazzup и Bitrix ===
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
CHANNEL_ID = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID = '77766961328'
ADMIN_CHAT_ID = '77778053727'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

# === Справочники ===
CITIES = {
    '1': 'Алматы', '2': 'Нур-Султан', '3': 'Шымкент',
    '4': 'Караганда', '5': 'Актобе', '6': 'Астана'
}

DIRECTIONS = {
    '1': 'Кирпич и блоки', '2': 'Цемент и растворы',
    '3': 'Арматура и металлопрокат', '4': 'Древесина и пиломатериалы',
    '5': 'Кровельные материалы', '6': 'Изоляция и утеплители',
    '7': 'Сантехника и водоснабжение', '8': 'Электрооборудование',
    '9': 'Инструменты', '10': 'Отделочные материалы'
}

RESPONSIBLES = {
    'Алматы': {'name': 'Менеджер Алматы', 'phone': '+7xxx', 'id': 2},
    'Нур-Султан': {'name': 'Менеджер Нур-Султана', 'phone': '+7xxx', 'id': 3},
    'Шымкент': {'name': 'Менеджер Шымкента', 'phone': '+7xxx', 'id': 4},
    'Караганда': {'name': 'Кирилл Костылев', 'phone': '+77766961328', 'id': 11},
    'Актобе': {'name': 'Менеджер Актобе', 'phone': '+7xxx', 'id': 5},
    'Астана': {'name': 'Менеджер Астаны', 'phone': '+77001234567', 'id': 1},
}

# === Модель базы данных ===
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50))
    fio = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    city = db.Column(db.String(50))
    direction = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# === Состояния пользователей и обработанные сообщения ===
user_states = {}
processed_message_ids = set()

# === Утилиты ===
def log(msg):
    print(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} - {msg}")

def send_message(chat_id: str, text: str) -> bool:
    headers = {'Authorization': f'Bearer {API_BEARER_TOKEN}', 'Content-Type': 'application/json'}
    payload = {
        "channelId": CHANNEL_ID,
        "chatType": "whatsapp",
        "chatId": chat_id,
        "text": text
    }
    try:
        r = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Wazzup Send ({chat_id}): {r.status_code}")
        return r.status_code in (200, 201)
    except Exception as e:
        log(f"Wazzup Error: {e}")
        return False

def notify_admin(fio, phone, city, event_type):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = (
        f"🔔 *Новая заявка* в Bitrix24\n"
        f"⏰ Время: {now}\n"
        f"👤 Клиент: {fio} ({phone})\n"
        f"🌆 Город: {city}\n"
        f"🎯 Цель: {event_type}\n"
        f"✅ Лид ожидает обработки в CRM."
    )
    send_message(ADMIN_CHAT_ID, text)

def create_bitrix_lead(city, event_type, fio, phone, chat_id):
    parts = fio.split(' ')
    last, first, second = (parts + ["", "", ""])[:3]
    assigned_id = RESPONSIBLES.get(city, {'id': 1})['id']
    comment = (
        f"Источник: WhatsApp Bot\nСобытие: {event_type}\nГород: {city}\n"
        f"Телефон клиента: {phone}\nКонтакт в WhatsApp: {fio}"
    )
    data = {
        "fields": {
            "TITLE": f"Optimus KZ Bot: {event_type} ({city})",
            "NAME": first, "LAST_NAME": last, "SECOND_NAME": second,
            "ASSIGNED_BY_ID": assigned_id,
            "ADDRESS_CITY": city, "COMMENTS": comment,
            "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }
    try:
        r = requests.post(BITRIX_WEBHOOK_URL, json=data, timeout=30)
        log(f"Bitrix lead: {r.status_code} / {r.text}")
        if r.status_code == 200 and r.json().get("result"):
            # Если лид успешно создан, сохраняем в базу
            db.session.add(Lead(chat_id=chat_id, fio=fio, phone=phone, city=city, direction=event_type))
            db.session.commit()
            notify_admin(fio, phone, city, event_type)
        else:
            send_message(chat_id, "⚠️ Проблема при сохранении заявки в CRM. Менеджер свяжется позже.")
    except Exception as e:
        log(f"Bitrix API error: {e}")
        send_message(chat_id, "⚠️ Не удалось соединиться с CRM. Попробуйте позже.")

# === Меню ===
def get_menu_text():
    return "👋 Добро пожаловать в *Optimus KZ*!\n\nВыберите город:\n" + \
        "\n".join(f"{k}. {v}" for k, v in CITIES.items())

def get_continue_menu():
    return "Спасибо! Чем можем помочь?\n1️⃣ — Подобрать товары\n2️⃣ — Обратный звонок"

def get_directions_menu():
    return "Выберите направление:\n" + \
        "\n".join(f"{k}. {v}" for k, v in DIRECTIONS.items())

# === Основной Webhook ===
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({'status': 'ready'}), 200

    data = request.get_json(force=True)
    for msg in data.get("messages", []):
        mid = msg.get("messageId")
        chat_id = msg.get("chatId")
        text = msg.get("text", "").strip()
        fio = msg.get("contact", {}).get("name", "Неизвестный")
        phone = msg.get("contact", {}).get("phone") or chat_id  # Берём телефон из contact, иначе chat_id
        is_me = msg.get("fromMe", False)
        is_echo = msg.get("isEcho", False)

        # Фильтры — пропускаем свои, эхо и уже обработанные сообщения
        if is_me or is_echo or not text or mid in processed_message_ids or chat_id != ALLOWED_CHAT_ID:
            processed_message_ids.add(mid)
            continue

        processed_message_ids.add(mid)
        state = user_states.get(chat_id, {"step": "city"})

        if state["step"] == "city":
            if text in CITIES:
                user_states[chat_id] = {"step": "menu", "city": CITIES[text]}
                send_message(chat_id, get_continue_menu())
            else:
                send_message(chat_id, get_menu_text())

        elif state["step"] == "menu":
            city = state["city"]
            if text == "1":
                user_states[chat_id]["step"] = "direction"
                send_message(chat_id, get_directions_menu())
            elif text == "2":
                send_message(chat_id, "📞 Ожидайте звонка менеджера.")
                create_bitrix_lead(city, "Callback", fio, phone, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_continue_menu())

        elif state["step"] == "direction":
            city = state["city"]
            if text in DIRECTIONS:
                direction = DIRECTIONS[text]
                send_message(chat_id,
                    f"🎯 Вы выбрали: *{direction}* в городе *{city}*. Менеджер свяжется с вами.")
                create_bitrix_lead(city, direction, fio, phone, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_directions_menu())

        else:
            user_states.pop(chat_id, None)
            send_message(chat_id, get_menu_text())

    return jsonify({'status': 'ok'}), 200

# === Проверка подключения к БД ===
@app.route('/ping-db')
def ping_db():
    try:
        count = Lead.query.count()
        return jsonify({"ok": True, "leads_count": count})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# === Запуск сервера ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    log("Сервер запущен, ожидаем webhook…")
    app.run(host='0.0.0.0', port=10000)
