from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    with open("log.txt", "a") as f:
        f.write(request.data.decode() + "\n\n")
    return "OK", 200

@app.route('/')
def index():
    with open("log.txt", "r") as f:
        return f"<pre>{f.read()}</pre>"
