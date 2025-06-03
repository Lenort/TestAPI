import datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Константы
EXPECTED_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
LOG_FILE = 'wazzup_log.txt'
CHANNEL_ID = 'fd738a59-6266-4aff-bdf4-bfa7420375ab'
ALLOWED_CHAT_ID = '77766961328'  # Только этот номер

WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

# Города
CITY_MAP = {
    "1": "Алматы",
    "2": "Астана",
    "3": "Шымкент",
    "4": "Караганда",
    "5": "Павлодар",
    "6": "Актобе"
}

# Состояния пользователей (в памяти)
user_states = {}

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

    try:
        messages = data.get("messages", [])
        for message in messages:
            chat_id = message.get("chatId") or message.get("chat_id")
            text = message.get("text", "").strip()

            if chat_id != ALLOWED_CHAT_ID:
                log(f"🚫 Игнорируем сообщение от {chat_id}")
                continue

            log(f"📨 Сообщение от {chat_id}: {text}")

            # Очистка состояния при новом запросе
            if text.lower() in ["город", "города", "start"]:
                user_states[chat_id] = "choosing"
                city_list = "\n".join([f"{k} — {v}" for k, v in CITY_MAP.items()])
                send_message(chat_id, f"Выберите город, отправив его номер:\n{city_list}")
                continue

            # Если в состоянии выбора — проверяем ввод
            if user_states.get(chat_id) == "choosing":
                if text in CITY_MAP:
                    send_message(chat_id, f"✅ Вы выбрали город: {CITY_MAP[text]}")
                    user_states[chat_id] = "selected"
                else:
                    send_message(chat_id, "Введите цифру от 1 до 6 для выбора города.")
            else:
                send_message(chat_id, "Введите 'город' чтобы начать выбор.")

    except Exception as e:
        log(f"⚠️ Ошибка при обработке сообщений: {e}")

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: str, text: str) -> bool:
    url = WAZZUP_SEND_API
    headers = {
        'Authorization': f'Bearer {EXPECTED_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "channelId": CHANNEL_ID,
        "chatType": "whatsapp",
        "chatId": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Отправка сообщения. Код ответа: {response.status_code}")
        print(f"Ответ сервера: {response.text}")
        if response.status_code in [200, 201]:
            log(f"✅ Сообщение отправлено на {chat_id}: {text}")
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
