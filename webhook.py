@app.route('/subscribe', methods=['POST'])
def subscribe():
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if token != EXPECTED_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
        url = data.get('url')
        events = data.get('events', ['message'])
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {e}'}), 400

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    payload = {
        "webhooksUri": url,
        "subscriptions": [
            {"subscriptions": events}
        ]
    }

    try:
        response = requests.patch(
            WAZZUP_WEBHOOKS_API,
            json=payload,
            headers={"Authorization": f"Bearer {EXPECTED_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            log(f"✅ Подписка на вебхуки успешна: {response.text}")
            return jsonify({'status': 'subscribed', 'response': response.json()}), 200
        else:
            log(f"❌ Ошибка подписки: {response.status_code} {response.text}")
            return jsonify({'error': 'Subscription failed', 'details': response.text}), response.status_code
    except Exception as e:
        log(f"❌ Исключение при подписке: {e}")
        return jsonify({'error': 'Exception during subscription', 'details': str(e)}), 500
