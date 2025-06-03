from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'

# Твой channelId для номера +77013092718 (отправитель)
CHANNEL_ID = 'fd738a59-6266-4aff-bdf4-bfa7420375ab'

WAZZUP_WEBHOOKS_API = 'https://api.wazzup24.com/v3/webhooks'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v2/messages/send'


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
        log(f"⚠️ Ошибка при разборе JSON: {e}")
        data = {}

    log(f"✅ Вебхук принят:\n{data}")

    # Парсим chatId и сообщение
    try:
        messages = data.get("messages", [])
        for message in messages:
            chat_id = message.get("chatId") or message.get("chat_id")
            from_ = message.get("from")
            text = message.get("text")

            if chat_id:
                print(f"[WAZZUP] Получено сообщение от CHAT_ID: {chat_id}")
                log(f"📬 Получено сообщение от CHAT_ID: {chat_id}")

            if from_ and text:
                log(f"📨 Сообщение от {from_} ({chat_id}): {text}")

                # Пример: автоматический ответ (если надо)
                # send_message(from_, "Спасибо за ваше сообщение!")

    except Exception as e:
        log(f"⚠️ Ошибка при извлечении chat_id или сообщений: {e}")

    return jsonify({'status': 'ok'}), 200


def send_message(phone: str, text: str) -> bool:
    # Убираем + если есть
    if phone.startswith('+'):
        phone = phone[1:]

    url = WAZZUP_SEND_API
    headers = {
        'Authorization': f'Bearer {EXPECTED_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "phone": phone,
        "channelId": CHANNEL_ID,
        "text": text
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Отправка сообщения. Код ответа: {response.status_code}")
        print(f"Ответ сервера: {response.text}")
        if response.status_code == 200:
            log(f"✅ Сообщение отправлено на {phone}: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки сообщения: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке сообщения: {e}")
        return False


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
