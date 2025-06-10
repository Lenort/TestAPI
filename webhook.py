from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} - {msg}")

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        log('GET /webhook - health check')
        return jsonify({'status': 'ready'}), 200

    # Авторизация по токену
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        log(f"❌ Unauthorized token: {token}")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        log(f"⚠️ Bad JSON: {e}")
        return jsonify({'error': 'bad json'}), 400

    log(f"✅ Webhook received: {data}")
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
