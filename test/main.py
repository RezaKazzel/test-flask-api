from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "API Flask di Railway!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json  # Ambil data JSON yang dikirim
    print("Webhook diterima:", data)  
    return jsonify({"status": "OK", "received": data}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
