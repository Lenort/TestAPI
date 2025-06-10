import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_FILE = 'wazzup_log.txt'
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} - {msg}\n")

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        log('GET /webhook - health check')
        return jsonify({'status': 'ready'}), 200

    # Проверяем токен авторизации
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        log(f"Unauthorized token: {token}")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        log(f"Bad JSON: {e}")
        return jsonify({'error': 'bad json'}), 400

    log(f"Webhook received: {data}")

    # Возвращаем 200 и фиксируем факт получения
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
