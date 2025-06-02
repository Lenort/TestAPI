from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
WAZZUP_WEBHOOKS_API = 'https://api.wazzup24.com/v3/webhooks'


@app.route('/', methods=['GET'])
def index():
    return 'Wazzup Webhook Listener is Running'


@app.route('/webhook', methods=['POST'])
def webhook():
    # Проверка заголовка авторизации
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

    if token != EXPECTED_TOKEN:
        log("❌ Неверный токен: " + token)
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        log(f"⚠️ Ошибка чтения JSON: {e}")
        return jsonify({'error': 'Invalid JSON'}), 400

    # Логирование запроса
    log("✅ Вебхук принят:\n" + str(data))

    return jsonify({'status': 'ok'}), 200


@app.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Этот endpoint инициирует подписку на вебхуки Wazzup.
    Ожидает JSON с параметрами подписки (url, events).
    """

    # Проверка авторизации запроса к самому приложению (можно убрать или сделать проще)
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    # Читаем параметры подписки из тела запроса
    try:
        data = request.get_json(force=True)
        url = data.get('url')
        events = data.get('events', ['messages'])
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {e}'}), 400

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Формируем тело PATCH-запроса на API Wazzup
    payload = {
        "url": url,
        "events": events,
        "token": EXPECTED_TOKEN
    }

    # Отправляем PATCH запрос для подписки
    try:
        response = requests.patch(WAZZUP_WEBHOOKS_API, json=payload, timeout=10)
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
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
