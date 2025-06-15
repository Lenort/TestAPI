from flask import Flask, request, jsonify
import datetime
import requests
import os
import psycopg2

app = Flask(__name__)

# === Настройки базы данных (Supabase) ===
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is not set")
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cursor = conn.cursor()

# === Настройки Wazzup ===
API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID        = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID   = '77766961328'   # бот отвечает только этому номеру
ADMIN_CHAT_ID     = '77778053727'
WAZZUP_SEND_API   = 'https://api.wazzup24.com/v3/message'

# === Настройки Bitrix24 ===
BITRIX_WEBHOOK_URL = 'https://b24-xq7bnn.bitrix24.kz/rest/1/tnjaxnh7k6xwbyyq/crm.lead.add.json'

# === Справочники ===
CITIES = {
    '1': 'Алматы','2': 'Нур-Султан','3': 'Шымкент',
    '4': 'Караганда','5': 'Актобе','6': 'Астана'
}
DIRECTIONS = {
    '1': 'Кирпич и блоки','2': 'Цемент и растворы','3': 'Арматура и металлопрокат',
    '4': 'Древесина и пиломатериалы','5': 'Кровельные материалы','6': 'Изоляция и утеплители',
    '7': 'Сантехника и водоснабжение','8': 'Электрооборудование','9': 'Инструменты',
    '10': 'Отделочные материалы'
}
RESPONSIBLES = {
    'Алматы': {'id':2},'Нур-Султан': {'id':3},'Шымкент': {'id':4},
    'Караганда': {'id':11},'Актобе': {'id':5},'Астана': {'id':1}
}

# Хранилище состояний и обработанных ID
user_states = {}
processed_message_ids = set()

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")

def save_or_update_user(chat_id, fio):
    """Запись или обновление пользователя в БД."""
    now = datetime.datetime.utcnow()
    cursor.execute("""
        INSERT INTO users (chat_id, fio, last_interaction)
        VALUES (%s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE
          SET last_interaction = EXCLUDED.last_interaction
    """, (chat_id, fio, now))

def send_message(chat_id: str, text: str) -> bool:
    headers = {
        'Authorization': f'Bearer {API_BEARER_TOKEN}',
        'Content-Type':  'application/json'
    }
    payload = {
        "channelId": CHANNEL_ID,
        "chatType":  "whatsapp",
        "chatId":    chat_id,
        "text":      text
    }
    try:
        r = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Отправка в Wazzup ({chat_id}): {r.status_code}")
        return r.status_code in (200, 201)
    except Exception as e:
        log(f"Ошибка отправки в Wazzup ({chat_id}): {e}")
        return False

def notify_admin(fio, phone, city, event_type):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = (
        f"🔔 *Новая заявка* в Bitrix24\n"
        f"⏰ {now}\n"
        f"👤 {fio} ({phone})\n"
        f"🌆 {city}\n"
        f"🎯 {event_type}\n"
        "✅ Лид ожидает обработки."
    )
    send_message(ADMIN_CHAT_ID, text)

def create_bitrix_lead(city, event_type, fio, phone, chat_id):
    parts = fio.split(' ')
    last, first, second = (parts + ["", "", ""])[:3]
    assigned = RESPONSIBLES.get(city, {'id':1})['id']
    comment = (
        f"Источник: WhatsApp Bot\n"
        f"Событие: {event_type}\n"
        f"Город: {city}\n"
        f"Телефон: {phone}\n"
        f"Контакт: {fio}"
    )
    data = {"fields":{
        "TITLE": f"Optimus KZ: {event_type} ({city})",
        "NAME": first, "LAST_NAME": last, "SECOND_NAME": second,
        "ASSIGNED_BY_ID": assigned, "ADDRESS_CITY": city,
        "COMMENTS": comment,
        "PHONE":[{"VALUE": phone,"VALUE_TYPE":"WORK"}]
    },"params":{"REGISTER_SONET_EVENT":"Y"}}
    try:
        r = requests.post(BITRIX_WEBHOOK_URL, json=data, timeout=30)
        log(f"Bitrix lead: {r.status_code}")
        if r.status_code==200 and r.json().get("result"):
            notify_admin(fio, phone, city, event_type)
    except Exception as e:
        log(f"Bitrix API error: {e}")

def get_menu_text():
    return "👋 Добро пожаловать в *Optimus KZ*!\nВыберите регион:\n" + \
           "\n".join(f"{k}. {v}" for k,v in CITIES.items())

def get_continue_menu():
    return "1️⃣ Подобрать товары\n2️⃣ Заказать звонок"

def get_directions_menu():
    return "Выберите направление:\n" + \
           "\n".join(f"{k}. {v}" for k,v in DIRECTIONS.items())

@app.route('/webhook', methods=['POST','GET'])
def webhook():
    if request.method=='GET':
        return jsonify({'status':'ready'}),200

    data = request.get_json(force=True)
    log(f"Webhook received: {data}")

    for msg in data.get("messages", []):
        mid     = msg.get("messageId")
        chat_id = msg.get("chatId")
        text    = msg.get("text","").strip()
        fio     = msg.get("contact",{}).get("name","Неизвестный")
        is_me   = msg.get("fromMe",False)
        is_echo = msg.get("isEcho",False)

        # ограничение по номеру
        if chat_id != ALLOWED_CHAT_ID:
            continue

        # сохраняем или обновляем пользователя
        save_or_update_user(chat_id, fio)

        # фильтрация: эхо, пустое, дубликаты
        if is_me or is_echo or not text or mid in processed_message_ids:
            processed_message_ids.add(mid)
            continue
        processed_message_ids.add(mid)

        state = user_states.get(chat_id,{"step":"city"})

        # Шаг 1: выбор города
        if state["step"]=="city":
            if text in CITIES:
                user_states[chat_id]={"step":"menu","city":CITIES[text]}
                send_message(chat_id,get_continue_menu())
            else:
                send_message(chat_id,get_menu_text())

        # Шаг 2: меню
        elif state["step"]=="menu":
            city = state["city"]
            if text=="1":
                user_states[chat_id]["step"]="direction"
                send_message(chat_id,get_directions_menu())
            elif text=="2":
                send_message(chat_id,"📞 Ожидайте звонка...")
                create_bitrix_lead(city,"Callback",fio,chat_id,chat_id)
                user_states.pop(chat_id,None)
            else:
                send_message(chat_id,get_continue_menu())

        # Шаг 3: направление
        elif state["step"]=="direction":
            city = state["city"]
            if text in DIRECTIONS:
                send_message(chat_id,f"🎯 {DIRECTIONS[text]} в {city}. Менеджер свяжется.")
                create_bitrix_lead(city,f"Direction: {DIRECTIONS[text]}",fio,chat_id,chat_id)
                user_states.pop(chat_id,None)
            else:
                send_message(chat_id,get_directions_menu())

        else:
            user_states.pop(chat_id,None)
            send_message(chat_id,get_menu_text())

    return jsonify({'status':'ok'}),200

if __name__=='__main__':
    log("Server started, waiting for webhook…")
    app.run(host='0.0.0.0',port=10000)
