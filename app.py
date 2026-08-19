from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "OK", 200
    if request.method == 'POST':
        data = request.json
        print("📩 Mensaje recibido:", data)
        return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Bot funcionando"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
