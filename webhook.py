from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

# === Настройки Wazzup ===
API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID        = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID   = '77766961328'
WAZZUP_SEND_API   = 'https://api.wazzup24.com/v3/message'

# === Настройки Bitrix24 ===
BITRIX_WEBHOOK_URL = 'https://b24-q1r4u7.bitrix24.kz/rest/1/2v6q3jv9k428rphg/crm.lead.add.json'

CITIES = {
    '1': 'Алматы',
    '2': 'Нур-Султан',
    '3': 'Шымкент',
    '4': 'Караганда',
    '5': 'Актобе',
    '6': 'Астана'      # добавил явный пункт
}

DIRECTIONS = {
    '1': 'Кирпич и Блоки',
    '2': 'Цемент и Растворы',
    '3': 'Арматура и Металлопрокат',
    '4': 'Древесина и Пиломатериалы',
    '5': 'Кровельные материалы',
    '6': 'Изоляция и Утеплители',
    '7': 'Сантехника и Водоснабжение',
    '8': 'Электрооборудование',
    '9': 'Инструменты',
    '10': 'Отделочные материалы'
}

user_states = {}               # хранит {'city': str, 'step': str}
processed_message_ids = set()

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")

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
        log(f"Отправка в Wazzup: {r.status_code}")
        return r.status_code in (200, 201)
    except Exception as e:
        log(f"Ошибка отправки в Wazzup: {e}")
        return False

def create_bitrix_lead(city, event_type, fio, phone):
    # разбиваем ФИО
    parts      = fio.split(' ')
    last, first, second = (parts + ["", "", ""])[:3]

    comment = f"Источник: WhatsApp Bot\nСобытие: {event_type}\nГород: {city}\nТелефон клиента: {phone}\nКонтакт в WhatsApp: {fio}"
    data = {
        "fields": {
            "TITLE":          f"Бот: {event_type} ({city})",
            "NAME":           first,
            "LAST_NAME":      last,
            "SECOND_NAME":    second,
            "ASSIGNED_BY_ID": 1,  # по умолчанию, если нужно — расширь под город
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
        log(f"Создание лида в Bitrix: {resp.status_code} / {resp.text}")
    except Exception as e:
        log(f"Ошибка Bitrix API: {e}")

def get_menu_text():
    return "Пожалуйста, выберите город:\n" + "\n".join(f"{k}. {v}" for k, v in CITIES.items())

def get_continue_menu():
    return ("Спасибо! Теперь выберите, что вы хотите сделать дальше:\n"
            "1. Выбрать направление (подбор товара)\n"
            "2. Заказать обратный звонок от менеджера")

def get_directions_menu():
    return "Выберите направление:\n" + "\n".join(f"{k}. {v}" for k, v in DIRECTIONS.items())

@app.route('/webhook', methods=['POST','GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({'status':'ready'}), 200

    data = request.get_json(force=True)
    log(f"Webhook recibido: {data}")

    for msg in data.get("messages", []):
        mid     = msg.get("messageId")
        chat_id = msg.get("chatId")
        text    = msg.get("text", "").strip()
        fio     = msg.get("contact", {}).get("name", "Неизвестный")
        is_me   = msg.get("fromMe", False)
        is_echo = msg.get("isEcho", False)

        log(f"Msg {mid} от {chat_id}: «{text}» (echo={is_echo}, fromMe={is_me})")

        if is_me or is_echo or not text or mid in processed_message_ids or chat_id != ALLOWED_CHAT_ID:
            log("Пропускаем это сообщение")
            processed_message_ids.add(mid)
            continue

        processed_message_ids.add(mid)
        state = user_states.get(chat_id, {"step":"city"})

        # ——— Шаг 1. Выбор города ———
        if state["step"] == "city":
            if text in CITIES:
                city = CITIES[text]
                user_states[chat_id] = {"step":"menu", "city":city}
                send_message(chat_id, f"Отлично! Вы выбрали *{city}*.\n" +
                                      get_continue_menu())
            else:
                send_message(chat_id, "Не распознал город.\n" + get_menu_text())

        # ——— Шаг 2. Главное меню ———
        elif state["step"] == "menu":
            if text == "1":
                user_states[chat_id]["step"] = "direction"
                send_message(chat_id, get_directions_menu())
            elif text == "2":
                city = state["city"]
                send_message(chat_id,
                    "Ожидайте, пожалуйста, звонок нашего менеджера в течение 15 минут.\n"
                    "Спасибо за обращение!")
                # создаём лид в Bitrix с типом «Callback»
                create_bitrix_lead(city, "Callback", fio, chat_id)
                user_states.pop(chat_id)  # закончено
            else:
                send_message(chat_id, get_continue_menu())

        # ——— Шаг 3. Выбор направления ———
        elif state["step"] == "direction":
            if text in DIRECTIONS:
                city      = state["city"]
                direction = DIRECTIONS[text]
                send_message(chat_id,
                    f"Вы выбрали направление *«{direction}»* в городе *{city}*.\n"
                    "Сейчас я подготовлю для вас подборку и наш менеджер свяжется для уточнения деталей.\n"
                    "Спасибо за ваш выбор!")
                # создаём лид «Direction» с указанием направления
                create_bitrix_lead(city, f"Direction: {direction}", fio, chat_id)
                user_states.pop(chat_id)  # закончено
            else:
                send_message(chat_id, "Неверный выбор, повторите:\n" + get_directions_menu())

        else:
            # сброс состояния и повтор меню
            user_states.pop(chat_id, None)
            send_message(chat_id, "Давайте начнём сначала.\n" + get_menu_text())

    return jsonify({'status':'ok'}), 200

if __name__ == '__main__':
    log("Сервер запущен, ожидаем webhook...")
    app.run(host='0.0.0.0', port=10000)
