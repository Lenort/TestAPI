from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
WAZZUP_WEBHOOKS_API = 'https://api.wazzup24.com/v3/webhooks'
WAZZUP_SEND_API = 'https://wazzup24.com/api/messages/send'  # URL из документации для отправки сообщений


@app.route('/', methods=['GET'])
def index():
    return 'Wazzup Webhook Listener is Running'


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200

    user_agent = request.headers.get('User-Agent', '').lower()

    if 'node-fetch' in user_agent:
        # Запрос от Wazzup - пропускаем проверку токена
        pass
    else:
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
    return jsonify({'status': 'ok'}), 200


@app.route('/subscribe', methods=['POST'])
def subscribe():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON'}), 400

    url = data.get('url')
    events = data.get('events', ['messagesAndStatuses'])

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    payload = {
        "webhooksUri": url,
        "subscriptions": {
            "messagesAndStatuses": True  # Так подписываемся согласно документации
        }
    }

    headers = {
        "Authorization": f"Bearer {EXPECTED_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(WAZZUP_WEBHOOKS_API, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            log(f"✅ Подписка на вебхуки успешна: {response.text}")
            return jsonify({'status': 'subscribed', 'response': response.json()}), 200
        else:
            log(f"❌ Ошибка подписки: {response.status_code} {response.text}")
            return jsonify({'error': 'Subscription failed', 'details': response.text}), response.status_code
    except Exception as e:
        log(f"❌ Исключение при подписке: {e}")
        return jsonify({'error': 'Exception during subscription', 'details': str(e)}), 500


@app.route('/send_message', methods=['POST'])
def send_message():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON'}), 400

    phone = data.get('phone')
    text = data.get('text')

    if not phone or not text:
        return jsonify({'error': 'Phone and text are required'}), 400

    payload = {
        "phone": phone if phone.startswith('+') else f"+{phone}",
        "text": text
    }

    headers = {
        "Authorization": f"Bearer {EXPECTED_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            log(f"✅ Сообщение отправлено на {phone}: {text}")
            return jsonify({'status': 'message sent', 'response': resp.json()}), 200
        else:
            log(f"❌ Ошибка отправки сообщения: {resp.status_code} {resp.text}")
            return jsonify({'error': 'Send failed', 'details': resp.text}), resp.status_code
    except Exception as e:
        log(f"❌ Исключение при отправке сообщения: {e}")
        return jsonify({'error': 'Exception during send', 'details': str(e)}), 500


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
