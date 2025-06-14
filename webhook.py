from flask import Flask, request, jsonify
import os
import datetime
import requests
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# === Настройки окружения ===
API_BEARER_TOKEN  = os.getenv('API_BEARER_TOKEN')
CHANNEL_ID         = os.getenv('CHANNEL_ID')
ALLOWED_CHAT_ID    = os.getenv('ALLOWED_CHAT_ID')
ADMIN_CHAT_ID      = os.getenv('ADMIN_CHAT_ID')
WAZZUP_SEND_API    = os.getenv('WAZZUP_SEND_API')
DATABASE_URL       = os.getenv('DATABASE_URL')

# === SQLAlchemy setup ===
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatRecord(Base):
    __tablename__ = 'chat_records'
    chat_id = Column(String, primary_key=True, index=True)
    user_phone = Column(String, nullable=True)
    last_bot_message = Column(DateTime, nullable=False)

# создаём таблицу при старте
Base.metadata.create_all(bind=engine)

app = Flask(__name__)

# === Справочники и остальной код ===
CITIES = {
    '1': 'Алматы', '2': 'Нур-Султан', '3': 'Шымкент',
    '4': 'Караганда', '5': 'Актобе', '6': 'Астана'
}
DIRECTIONS = {
    '1': 'Кирпич и блоки', '2': 'Цемент и растворы', '3': 'Арматура и металлопрокат',
    '4': 'Древесина и пиломатериалы', '5': 'Кровельные материалы',
    '6': 'Изоляция и утеплители', '7': 'Сантехника и водоснабжение',
    '8': 'Электрооборудование', '9': 'Инструменты', '10': 'Отделочные материалы'
}
RESPONSIBLES = {
    'Алматы': {'name': 'Менеджер Алматы', 'phone': '+7xxx', 'id': 2},
    'Нур-Султан': {'name': 'Менеджер Нур-Султана', 'phone': '+7xxx', 'id': 3},
    'Шымкент': {'name': 'Менеджер Шымкента', 'phone': '+7xxx', 'id': 4},
    'Караганда': {'name': 'Кирилл Костылев', 'phone': '+77766961328', 'id': 11},
    'Актобе': {'name': 'Менеджер Актобе', 'phone': '+7xxx', 'id': 5},
    'Астана': {'name': 'Менеджер Астаны', 'phone': '+77001234567', 'id': 1},
}

# === Функция для записи в БД ===
def record_chat_event(chat_id: str, user_phone: str = None):
    session = SessionLocal()
    try:
        now = datetime.datetime.now()
        record = session.query(ChatRecord).get(chat_id)
        if record:
            record.last_bot_message = now
            if user_phone:
                record.user_phone = user_phone
        else:
            record = ChatRecord(
                chat_id=chat_id,
                user_phone=user_phone,
                last_bot_message=now
            )
            session.add(record)
        session.commit()
    finally:
        session.close()

# === Основные функции бота ===

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")


def send_message(chat_id: str, text: str) -> bool:
    headers = {
        'Authorization': f'Bearer {API_BEARER_TOKEN}',
        'Content-Type':  'application/json'
    }
    payload = {"channelId": CHANNEL_ID, "chatType": "whatsapp", "chatId": chat_id, "text": text}
    try:
        r = requests.post(WAZZUP_SEND_API, json=payload, headers=headers, timeout=30)
        log(f"Отправка в Wazzup ({chat_id}): {r.status_code}")
        return r.status_code in (200, 201)
    except Exception as e:
        log(f"Ошибка отправки в Wazzup ({chat_id}): {e}")
        return False

# функции меню

def get_menu_text():
    return (
        "👋 Добро пожаловать в *Optimus KZ*! 👋\n\n"
        "Для начала выберите ваш регион, чтобы мы могли подобрать "
        "регионального менеджера:\n" +
        "\n".join(f"{k}. {v}" for k, v in CITIES.items())
    )

def get_continue_menu():
    return (
        "Спасибо! Чем мы можем помочь дальше?\n"
        "1️⃣ — Подобрать товары по направлению\n"
        "2️⃣ — Заказать обратный звонок от менеджера"
    )

def get_directions_menu():
    return (
        "Выберите направление подбора:\n" +
        "\n".join(f"{k}. {v}" for k, v in DIRECTIONS.items()) +
        "\n\n(Просто отправьте номер пункта)"
    )

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({'status': 'ready'}), 200

    data = request.get_json(force=True)
    log(f"Webhook received: {data}")

    for msg in data.get("messages", []):
        mid     = msg.get("messageId")
        chat_id = msg.get("chatId")
        text    = msg.get("text", "").strip()
        fio     = msg.get("contact", {}).get("name", "Неизвестный")
        is_me   = msg.get("fromMe", False)
        is_echo = msg.get("isEcho", False)

        log(f"Msg {mid} from {chat_id}: «{text}» (echo={is_echo}, fromMe={is_me})")

        # фильтры
        if is_me or is_echo or not text or chat_id != ALLOWED_CHAT_ID:
            continue

        state = user_states.get(chat_id, {"step": "city"})

        # Шаг 1: выбор города
        if state["step"] == "city":
            if text in CITIES:
                city = CITIES[text]
                user_states[chat_id] = {"step": "menu", "city": city}
                if send_message(chat_id, get_continue_menu()):
                    # при переходе к меню ничего не сохраняем
                    pass
            else:
                send_message(chat_id, get_menu_text())

        # Шаг 2: главное меню
        elif state["step"] == "menu":
            city = state["city"]
            if text == "1":
                user_states[chat_id]["step"] = "direction"
                send_message(chat_id, get_directions_menu())
            elif text == "2":
                if send_message(chat_id,
                    "📞 Ожидайте звонок нашего регионального менеджера в течение 15 минут.\n"
                    "Спасибо за обращение в *Optimus KZ*!" ):
                    # записываем событие "callback"
                    record_chat_event(chat_id, fio)
                create_bitrix_lead(city, "Callback", fio, chat_id, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_continue_menu())

        # Шаг 3: выбор направления
        elif state["step"] == "direction":
            city = state["city"]
            if text in DIRECTIONS:
                direction = DIRECTIONS[text]
                if send_message(chat_id,
                    f"🎯 Вы выбрали: *{direction}* в городе *{city}*.\n"
                    "Наш менеджер подготовит для вас подборку и свяжется "
                    "для уточнения деталей. Спасибо, что выбрали *Optimus KZ*!" ):
                    # записываем событие "direction"
                    record_chat_event(chat_id, fio)
                create_bitrix_lead(city, f"Direction: {direction}", fio, chat_id, chat_id)
                user_states.pop(chat_id, None)
            else:
                send_message(chat_id, get_directions_menu())

        # Сброс
        else:
            user_states.pop(chat_id, None)
            send_message(chat_id, get_menu_text())

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    log("Сервер запущен, ожидаем webhook…")
    app.run(host='0.0.0.0', port=10000)
