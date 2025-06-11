from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

API_BEARER_TOKEN = ''  # Вставь свой токен
CHANNEL_ID = 'c1808feb-0822-4203-a6dc-e2a07c705751'
ALLOWED_CHAT_ID = '77766961328'
WAZZUP_SEND_API = 'https://api.wazzup24.com/v3/message'

# Города для выбора по цифрам
CITIES = {
    '1': 'Алматы',
    '2': 'Нур-Султан',
    '3': 'Шымкент',
    '4': 'Караганда',
    '5': 'Актобе'
}

# Направления для строительного магазина (будут 10 пунктов)
DIRECTIONS = {
    '1': 'Кирпич и Блоки',
    '2': 'Цемент и Растворы',
    '3': 'Арматура и Металлопрокат',
    '4': 'Древесина и Пиломатериалы',
    '5': 'Кровельные материалы',
    '6': 'Изоляция и Утеплители',
    '7': 'Сантехника и Водоснабжение',
    '8': 'Электрооборудование',
    '9': 'Инструменты',
    '10': 'Отделочные материалы'
}

# Состояния пользователя
user_states = {}  # {chat_id: {'city': str, 'step': 'city'|'menu'|'direction'|...}}
processed_message_ids = set()


def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{now} - {msg}")


def get_menu_text():
    lines = ['Выберите город, отправив цифру:']
    for key, city in CITIES.items():
        lines.append(f"{key}. {city}")
    return '\n'.join(lines)


def get_continue_menu():
    return 'Желаете продолжить?\n1. Выбор направлений\n2. Заказать звонок'


def get_directions_menu():
    lines = ['Выберите направление, отправив цифру:']
    for key, name in DIRECTIONS.items():
        lines.append(f"{key}. {name}")
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
            is_echo = message.get("isEcho", False)
            message_id = message.get("messageId")

            log(f"Сообщение от {chat_id}, fromMe={from_me}, isEcho={is_echo}: {text}")

            if from_me or is_echo:
                log("Эхо или сообщение от бота, пропускаем")
                continue
            if message_id in processed_message_ids:
                log(f"Повторное сообщение (id: {message_id}), пропускаем")
                continue
            processed_message_ids.add(message_id)
            if chat_id != ALLOWED_CHAT_ID or not text:
                log(f"Пропускаем сообщение с chatId={chat_id} или пустой текст")
                continue

            # Инициализируем состояние, если новый пользователь
            if chat_id not in user_states:
                user_states[chat_id] = {'city': None, 'step': 'city'}

            state = user_states[chat_id]

            # Шаг выбора города
            if state['step'] == 'city':
                if text in CITIES:
                    city = CITIES[text]
                    state['city'] = city
                    state['step'] = 'menu'
                    send_message(chat_id, f"Вы выбрали город: {city}")
                    # --- Начало области доработки: меню продолжения ---
                    send_message(chat_id, get_continue_menu())  # TODO: Обработать выбор 1/2
                    # --- Конец области доработки ---
                else:
                    send_message(chat_id, f"Не понял вас.\n{get_menu_text()}")

            # Шаг меню продолжения и далее — будут допиливаться позже
            elif state['step'] == 'menu':
                # TODO: Обработать выбор 1 (directions) и 2 (callback)
                # Если пользователь выбрал '2' (заказать звонок):
                #   send_message(chat_id, "В ближайшее время региональный менеджер с вами свяжется.")
                #   state['step'] = 'done'
                # Если '1' — перейти к выбору направления:
                #   state['step'] = 'direction'
                #   send_message(chat_id, get_directions_menu())
                pass

            # Шаг выбора направления
            elif state['step'] == 'direction':
                # TODO: Обработать выбор направления (10 пунктов)
                # После выбора отправить "Спасибо за обратную связь" и state['step']='done'
                pass

            # Шаг завершён
            elif state['step'] == 'done':
                log("Диалог завершён, игнорируем ввод пользователя")

    except Exception as e:
        log(f"⚠️ Ошибка при обработке сообщения: {e}")

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    log("Сервер запущен, ожидаем webhook...")
    app.run(host='0.0.0.0', port=10000)
