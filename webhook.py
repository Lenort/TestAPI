from flask import Flask, request, jsonify
import datetime
import requests
import os

app = Flask(__name__)

EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
WAZZUP_WEBHOOKS_API = 'https://api.wazzup24.com/v3/webhooks'


@app.route('/', methods=['GET'])
def index():
    return 'Wazzup Webhook Listener is Running'


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200

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
    events = data.get('events', ['message'])

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    payload = {
        "webhooksUri": url,
        "subscriptions": [
            {"events": events}
        ]
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


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{now} — {message}"
    print(full_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_message + "\n")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
