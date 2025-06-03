import datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
CHANNEL_ID = 'fd738a59-6266-4aff-bdf4-bfa7420375ab'
ALLOWED_CHAT_ID = '77766961328'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

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
    if 'node-fetch' not in user_agent:
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

            if chat_id != ALLOWED_CHAT_ID or not text:
                continue

            if last_messages.get(chat_id) == text:
                continue
            last_messages[chat_id] = text

            log(f"📨 Принято новое сообщение от {chat_id}: {text}")
            # send_message(chat_id, "Принято ✅")  # ОТПРАВКА ОТКЛЮЧЕНА

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
        print(f"Отправка сообщения. Код ответа: {response.status_code}")
        print(f"Ответ сервера: {response.text}")
        if response.status_code in [200, 201]:
            log(f"✅ Отправлено [{chat_id}]: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке: {e}")
        return False


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
