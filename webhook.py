from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'

# channelId для номера +77013092718
CHANNEL_ID = 'fd738a59-6266-4aff-bdf4-bfa7420375ab'

def log(message: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} — {message}\n")

def send_message(phone: str, text: str):
    url = 'https://api.wazzup24.com/v2/messages/send'
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
        if response.status_code == 200:
            log(f"✅ Сообщение отправлено на {phone}: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки сообщения: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке сообщения: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ready"})

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
            text = message.get("text") or message.get("body", {}).get("text", "(текст не найден)")

            print(f"[WAZZUP] CHAT_ID: {chat_id}, FROM: {from_}, TEXT: {text}")
            log(f"📨 Сообщение от {from_} ({chat_id}): {text}")

            # Пример — отправляем ответ на номер +77766961328
            # Здесь можешь менять условие, когда слать сообщение
            if from_ == '77766961328':
                send_message(from_, f"Привет! Я получил твоё сообщение: {text}")

    except Exception as e:
        log(f"⚠️ Ошибка при извлечении chat_id: {e}")

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
