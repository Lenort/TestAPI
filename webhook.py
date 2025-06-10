from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} - {msg}")

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
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
