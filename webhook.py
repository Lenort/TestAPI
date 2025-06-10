# webhook.py

import datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
CHANNEL_ID = 'fd738a59-6266-4aff-bdf4-bfa7420375ab'
ALLOWED_CHAT_ID = '77780504505'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'
WAZZUP_WEBHOOK_API = 'https://api.wazzup24.com/v3/webhooks'
WEBHOOK_URL = 'https://dashboard.render.com/webhook'

# Города для выбора по цифрам
CITIES = {
    '1': 'Москва',
    '2': 'Санкт-Петербург',
    '3': 'Новосибирск',
    '4': 'Екатеринбург',
    '5': 'Казань'
}

# Формирование меню
def get_menu_text():
    menu_lines = ['Выберите город, отправив цифру:']
    for key, city in CITIES.items():
        menu_lines.append(f"{key}. {city}")
    return '\n'.join(menu_lines)

# Хранилище последних сообщений
last_messages = {}

@app.route('/', methods=['GET'])
def index():
    return 'Wazzup Webhook Listener is Running'

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200

    user_agent = request.headers.get('User-Agent', '').lower()
    if 'node-fetch' in user_agent:
        return jsonify({'status': 'ignored'}), 200

    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        log(f"❌ Неверный токен: {token}")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        log(f"⚠️ Ошибка JSON: {e}")
        return jsonify({'error': 'bad json'}), 400

    log(f"✅ Вебхук принят:\n{data}")

    try:
        messages = data.get("messages", [])
        for message in messages:
            chat_id = message.get("chatId") or message.get("chat_id")
            text = message.get("text", "").strip()

            if not chat_id or not text:
                continue
            if chat_id != ALLOWED_CHAT_ID:
                log(f"🚫 Игнорируем сообщение от {chat_id}")
                continue

            # Предотвращаем повторную обработку
            if last_messages.get(chat_id) == text:
                continue
            last_messages[chat_id] = text

            # Печать в консоль — от кого и что
            print(f"📥 Получено от {chat_id}: {text}")
            log(f"📨 Принято новое сообщение от {chat_id}: {text}")

            if text in CITIES:
                send_message(chat_id, CITIES[text])
            else:
                send_message(chat_id, "Не понял вас. Попробуйте ещё раз.\n" + get_menu_text())

    except Exception as e:
        log(f"⚠️ Ошибка при обработке: {e}")

    return jsonify({'status': 'ok'}), 200


def send_message(chat_id: str, text: str) -> bool:
    headers = {
        'Authorization': f'Bearer {EXPECTED_TOKEN}',
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
        print(f"📤 Отправка сообщения. Код ответа: {response.status_code}")
        print(f"📤 Ответ сервера: {response.text}")
        if response.status_code in [200, 201]:
            log(f"✅ Отправлено [{chat_id}]: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке: {e}")
        return False


def register_webhook():
    headers = {
        'Authorization': f'Bearer {EXPECTED_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "url": WEBHOOK_URL,
        "events": ["messages"]
    }

    try:
        response = requests.patch(WAZZUP_WEBHOOK_API, json=payload, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            print("✅ Вебхук успешно зарегистрирован")
            log("✅ Вебхук успешно зарегистрирован")
        else:
            print(f"⚠️ Ошибка регистрации вебхука: {response.status_code} {response.text}")
            log(f"⚠️ Ошибка регистрации вебхука: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Исключение при регистрации вебхука: {e}")
        log(f"❌ Исключение при регистрации вебхука: {e}")


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")


if __name__ == '__main__':
    log(get_menu_text())
    register_webhook()
    app.run(host='0.0.0.0', port=10000)
