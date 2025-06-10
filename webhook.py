from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

LOG_FILE = 'wazzup_log.txt'
API_BEARER_TOKEN = '92a8247c0ce7472a86a5c36f71327d19'
CHANNEL_ID = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID = '77766961328'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

CITIES = {
    '1': 'Алматы',
    '2': 'Нур-Султан',
    '3': 'Шымкент',
    '4': 'Караганда',
    '5': 'Актобе'
}

last_messages = {}
user_states = {}

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} - {msg}")

def get_menu_text():
    lines = ['Выберите город, отправив цифру:']
    for key, city in CITIES.items():
        lines.append(f"{key}. {city}")
    return '\n'.join(lines)

def send_message(chat_id: str, text: str) -> bool:
    headers = {
        'Authorization': f'Bearer {API_BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "channelId": CHANNEL_ID,
        "chatType": "whatsapp",
        "chatId": chat_id,
        "text": text
    }
    try:
        response = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Отправка сообщения на {chat_id}. Код ответа: {response.status_code}")
        if response.status_code in [200, 201]:
            log(f"✅ Отправлено [{chat_id}]: {text}")
            return True
        else:
            log(f"❌ Ошибка отправки: {response.status_code} {response.text}")
            return False
    except Exception as e:
        log(f"❌ Исключение при отправке: {e}")
        return False

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

    try:
        messages = data.get("messages", [])
        for message in messages:
            chat_id = message.get("chatId")
            text = message.get("text", "").strip()
            from_me = message.get("fromMe", False)

            log(f"Сообщение от {chat_id}, fromMe={from_me}: {text}")

            if from_me:
                log("Сообщение от бота, пропускаем")
                continue

            if chat_id != ALLOWED_CHAT_ID:
                log(f"Пропускаем сообщение с chatId={chat_id}")
                continue
            if not text:
                log("Пустой текст, пропускаем")
                continue

            if last_messages.get(chat_id) == text:
                log("Повтор сообщения, пропускаем")
                continue
            last_messages[chat_id] = text

            user_state = user_states.get(chat_id)

            if user_state is None:
                if text in CITIES:
                    city = CITIES[text]
                    user_states[chat_id] = city
                    send_message(chat_id, f"Вы выбрали город: {city}")
                else:
                    send_message(chat_id, "Не понял вас. Попробуйте ещё раз.\n" + get_menu_text())
            else:
                if text.lower() == 'сброс':
                    user_states[chat_id] = None
                    send_message(chat_id, get_menu_text())
                else:
                    log(f"Пользователь уже выбрал город {user_state}, сообщение проигнорировано: {text}")

    except Exception as e:
        log(f"⚠️ Ошибка при обработке сообщения: {e}")

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    log("Сервер запущен, ожидаем webhook...")
    app.run(host='0.0.0.0', port=10000)
