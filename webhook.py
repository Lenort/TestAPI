@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200

    user_agent = request.headers.get('User-Agent', '').lower()

    # Проверка токена, если это не запрос от Wazzup
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

    # 📤 ПАРСИМ CHAT ID, номер и текст
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
