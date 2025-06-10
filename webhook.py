@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        print('GET /webhook - health check')
        return jsonify({'status': 'ready'}), 200

    # 🔧 Временно отключено — можно включить позже
    # auth = request.headers.get('Authorization', '')
    # token = auth.replace('Bearer ', '').strip()
    # if token != EXPECTED_TOKEN:
    #     print(f"Unauthorized token: {token}")
    #     return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"❌ Bad JSON: {e}")
        return jsonify({'error': 'bad json'}), 400

    print(f"✅ Webhook received: {data}")

    return jsonify({'status': 'ok'}), 200
