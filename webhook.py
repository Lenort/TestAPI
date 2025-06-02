from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Webhook сервис работает!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"Получен webhook: {data}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Ошибка при обработке webhook: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
