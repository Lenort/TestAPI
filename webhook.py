from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'

def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")

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

    try:
        messages = data.get("messages", [])
        for message in messages:
            chat_id = message.get("chatId") or message.get("chat_id")
            from_ = message.get("from", "неизвестно")
            text = message.get("text", "(без текста)")

            if chat_id:
                print(f"[WAZZUP] Получено сообщение от CHAT_ID: {chat_id}")
                log(f"📬 Получено сообщение от CHAT_ID: {chat_id}")
                log(f"📨 Сообщение от {from_} ({chat_id}): {text}")
    except Exception as e:
        log(f"⚠️ Ошибка при извлечении chat_id или данных сообщения: {e}")

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
