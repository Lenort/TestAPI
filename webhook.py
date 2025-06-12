from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

# === Настройки Wazzup ===
API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID        = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID   = '77766961328'
ADMIN_CHAT_ID     = '77778053727'   # сюда будут приходить уведомления
WAZZUP_SEND_API   = 'https://api.wazzup24.com/v3/message'

# === Настройки Bitrix24 ===
BITRIX_WEBHOOK_URL = 'https://b24-xq7bnn.bitrix24.kz/rest/1/tnjaxnh7k6xwbyyq/crm.lead.add.json'

# === Справочники ===
CITIES = {
    '1': 'Алматы',
    '2': 'Нур-Султан',
    '3': 'Шымкент',
    '4': 'Караганда',
    '5': 'Актобе',
    '6': 'Астана'
}

DIRECTIONS = {
    '1': 'Кирпич и блоки',
    '2': 'Цемент и растворы',
    '3': 'Арматура и металлопрокат',
    '4': 'Древесина и пиломатериалы',
    '5': 'Кровельные материалы',
    '6': 'Изоляция и утеплители',
    '7': 'Сантехника и водоснабжение',
    '8': 'Электрооборудование',
    '9': 'Инструменты',
    '10': 'Отделочные материалы'
}

# === Ответственные за города ===
RESPONSIBLES = {
    'Алматы':     {'name': 'Менеджер Алматы',     'phone': '+7xxx', 'id': 2},
    'Нур-Султан': {'name': 'Менеджер Нур-Султана','phone': '+7xxx', 'id': 3},
    'Шымкент':    {'name': 'Менеджер Шымкента',   'phone': '+7xxx', 'id': 4},
    'Караганда':  {'name': 'Кирилл Костылев',     'phone': '+77766961328', 'id': 11},
    'Актобе':     {'name': 'Менеджер Актобе',     'phone': '+7xxx', 'id': 5},
    'Астана':     {'name': 'Менеджер Астаны',     'phone': '+77001234567', 'id': 1},
}

# Хранилище состояний и обработанных ID
user_states = {}
processed_message_ids = set()

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")

def send_message(chat_id: str, text: str) -> bool:
    """Отправка текста в Wazzup"""
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
    """Уведомление администратора о новом лидe"""
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
    """Создание лида в Bitrix и уведомление админа"""
    parts = fio.split(' ')
    last, first, second = (parts + ["", "", ""])[:3]
    resp = RESPONSIBLES.get(city, {'id': 1})
    assigned_id = resp['id']

    comment = (
        f"Источник: WhatsApp Bot\n"
        f"Событие: {event_type}\n"
        f"Город: {city}\n"
        f"Телефон клиента: {phone}\n"
        f"Контакт в WhatsApp: {fio}"
    )
    data = {
        "fields": {
            "TITLE":          f"Optimus KZ Bot: {event_type} ({city})",
            "NAME":           first,
            "LAST_NAME":      last,
            "SECOND_NAME":    second,
            "ASSIGNED_BY_ID": assigned_id,
            "ADDRESS_CITY":   city,
            "COMMENTS":       comment,
            "PHONE": [
                {"VALUE": phone, "VALUE_TYPE": "WORK"}
            ],
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }
    try:
        resp = requests.post(BITRIX_WEBHOOK_URL, json=data, timeout=30)
        log(f"Bitrix lead: {resp.status_code} / {resp.text}")
        if resp.status_code == 200 and resp.json().get("result"):
            notify_admin(fio, phone, city, event_type)
        else:
            send_message(chat_id,
                "⚠️ При сохранении заявки в CRM возникла проблема. "
                "Менеджер свяжется с вами в ближайшее время.")
    except Exception as e:
        log(f"Bitrix API error: {e}")
        send_message(chat_id,
            "⚠️ Не удалось соединиться с CRM. Попробуйте позже.")

def get_menu_text():
    return (
        "👋 Добро пожаловать в *Optimus KZ*! 👋\n\n"
        "Для начала выберите ваш регион, чтобы мы могли подобрать "
        "регионального менеджера:\n" +
        "\n".join(f"{k}. {v}" for k, v in CITIES.items())
    )

def get_continue_menu():
    return (
        "Спасибо! Чем мы можем помочь дальше?\n"
        "1️⃣ — Подобрать товары по направлению\n"
        "2️⃣ — Заказать обратный звонок от менеджера"
    )

def get_directions_menu():
    return (
        "Выберите направление подбора:\n" +
        "\n".join(f"{k}. {v}" for k, v in DIRECTIONS.items()) +
        "\n\n(Просто отправьте номер пункта)"
    )

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
        is_me   = msg.get("fromMe", False)
        is_echo = msg.get("isEcho", False)

        log(f"Msg {mid} from {chat_id}: «{text}» (echo={is_echo}, fromMe={is_me})")

        if is_me or is_echo or not text or mid in processed_message_ids or chat_id != ALLOWED_CHAT_ID:
            processed_message_ids.add(mid)
            continue

        processed_message_ids.add(mid)
        state = user_states.get(chat_id, {"step": "city"})

        # Шаг 1: выбор города
        if state["step"] == "city":
            if text in CITIES:
                city = CITIES[text]
                user_states[chat_id] = {"step": "menu", "city": city}
                send_message(chat_id, get_continue_menu())
            else:
                send_message(chat_id, get_menu_text())

        # Шаг 2: главное меню
        elif state["step"] == "menu":
            city = state["city"]
            if text == "1":
                user_states[chat_id]["step"] = "direction"
                send_message(chat_id, get_directions_menu())
            elif text == "2":
                send_message(chat_id,
                    "📞 Ожидайте звонок нашего регионального менеджера в течение 15 минут.\n"
                    "Спасибо за обращение в *Optimus KZ*!")
                create_bitrix_lead(city, "Callback", fio, chat_id, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_continue_menu())

        # Шаг 3: выбор направления
        elif state["step"] == "direction":
            city = state["city"]
            if text in DIRECTIONS:
                direction = DIRECTIONS[text]
                send_message(chat_id,
                    f"🎯 Вы выбрали: *{direction}* в городе *{city}*.\n"
                    "Наш менеджер подготовит для вас подборку и свяжется "
                    "для уточнения деталей. Спасибо, что выбрали *Optimus KZ*!")
                create_bitrix_lead(city, f"Direction: {direction}", fio, chat_id, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_directions_menu())

        # Сброс, если что-то пошло не так
        else:
            user_states.pop(chat_id, None)
            send_message(chat_id, get_menu_text())

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    log("Сервер запущен, ожидаем webhook…")
    app.run(host='0.0.0.0', port=10000)
