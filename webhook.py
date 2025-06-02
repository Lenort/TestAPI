from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'


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


def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{now} — {message}"
    print(full_message)  # Вывод в stdout, чтобы видеть в логах Render
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_message + "\n")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
