from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID = '77766961328'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

CITIES = {
    '1': 'Алматы',
    '2': 'Нур-Султан',
    '3': 'Шымкент',
    '4': 'Караганда',
    '5': 'Актобе'
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

user_states = {}
processed_message_ids = set()

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} - {msg}")

def get_menu_text():
    return '\n'.join([f"{k}. {v}" for k, v in CITIES.items()])

def get_continue_menu():
    return 'Желаете продолжить?\n1. Выбор направлений\n2. Заказать звонок'

def get_directions_menu():
    return '\n'.join([f"{k}. {v}" for k, v in DIRECTIONS.items()])

def send_message(chat_id: str, text: str) -> bool:
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
        response = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Отправка сообщения на {chat_id}. Код ответа: {response.status_code}")
        if response.status_code in [200, 201]:
            log(f"✅ Отправлено [{chat_id}]: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке: {e}")
        return False

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        log('GET /webhook - health check')
        return jsonify({'status': 'ready'}), 200

    try:
        data = request.get_json(force=True)
    except Exception as e:
        log(f"⚠️ Bad JSON: {e}")
        return jsonify({'error': 'bad json'}), 400

    log(f"✅ Webhook received: {data}")

    messages = data.get("messages", [])
    for message in messages:
        chat_id = message.get("chatId")
        text = message.get("text", "").strip()
        from_me = message.get("fromMe", False)
        is_echo = message.get("isEcho", False)
        message_id = message.get("messageId")

        log(f"Сообщение от {chat_id}, fromMe={from_me}, isEcho={is_echo}: {text}")

        if from_me or is_echo or not text:
            log("Эхо, пустое или сообщение от бота, пропускаем")
            continue
        if message_id in processed_message_ids:
            log(f"Повторное сообщение (id: {message_id}), пропускаем")
            continue
        processed_message_ids.add(message_id)

        state = user_states.get(chat_id, {'step': 'city'})

        if state['step'] == 'city':
            if text in CITIES:
                city = CITIES[text]
                user_states[chat_id] = {'city': city, 'step': 'menu'}
                send_message(chat_id, f"Вы выбрали город: {city}")
                send_message(chat_id, get_continue_menu())
            else:
                send_message(chat_id, "Не понял вас.\n" + get_menu_text())
        elif state['step'] == 'menu':
            if text == '1':
                user_states[chat_id]['step'] = 'direction'
                send_message(chat_id, get_directions_menu())
            elif text == '2':
                user_states[chat_id]['step'] = 'call'
                send_message(chat_id, "Наш специалист скоро свяжется с вами.")
            else:
                send_message(chat_id, "Пожалуйста, выберите:\n1. Выбор направлений\n2. Заказать звонок")
        elif state['step'] == 'direction':
            if text in DIRECTIONS:
                direction = DIRECTIONS[text]
                send_message(chat_id, f"Вы выбрали: {direction}\nСпасибо за выбор! Чем ещё можем помочь?")
                user_states[chat_id]['step'] = 'menu'  # вернуться в меню
                send_message(chat_id, get_continue_menu())
            else:
                send_message(chat_id, "Неверный выбор. Повторите:\n" + get_directions_menu())
        elif state['step'] == 'call':
            send_message(chat_id, "Ожидайте звонка от нашего специалиста.")
        else:
            user_states[chat_id] = {'step': 'city'}
            send_message(chat_id, "Начнём сначала.\n" + get_menu_text())

    return jsonify({'status': 'ok'}), 200
