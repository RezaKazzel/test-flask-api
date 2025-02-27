from flask import Flask, request, jsonify

app = Flask(__name__)

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1344385105774252052/Ty6imbzcU49d-vghGi6miUhbG1Vzlvho9WzRwRfAigQVDPS9pzFlHnfJF2D2Zz2grphF"

@app.route('/send_to_discord', methods=['POST'])
def send_to_discord():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Ambil data dari request
    sender = data.get("query", {}).get("sender", "Unknown")
    message = data.get("query", {}).get("message", "No message")
    is_group = data.get("query", {}).get("isGroup", False)

    # Format pesan untuk Discord
    discord_message = f"📩 **Pesan Baru**\n👤 Pengirim: {sender}\n💬 Pesan: {message}\n🏷️ Grup: {'Ya' if is_group else 'Tidak'}"

    # Kirim ke Webhook Discord
    payload = {"content": discord_message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

    # Periksa apakah pengiriman berhasil
    if response.status_code == 204:
        return jsonify({"status": "success", "message": "Sent to Discord"}), 200
    else:
        return jsonify({"status": "failed", "error": response.text}), response.status_code

@app.route('/testwa', methods=['POST'])
def new_receive_message():
    data = request.get_json()  # Ambil data JSON dari request
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Cetak data yang diterima (opsional)
    print(f"Pesan diterima dari {data.get('sender')}: {data.get('message')}")

    # Balas dengan JSON
    response = {
        "reply": "Hi, we have received your request in the new endpoint, thanks!"
    }
    return jsonify(response), 200  # HTTP 200 OK

@app.route('/receive_message', methods=['POST'])
def receive_message():
    data = request.get_json()  # Ambil data JSON dari request
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Ambil informasi dari JSON yang dikirim
    app_package = data.get("appPackageName", "Unknown")
    messenger = data.get("messengerPackageName", "Unknown")
    query = data.get("query", {})

    sender = query.get("sender", "Unknown")
    message = query.get("message", "No message")
    is_group = query.get("isGroup", False)

    # Cetak ke console (opsional)
    print(f"Pesan diterima dari {sender}: {message} (Group: {is_group})")

    # Buat respons JSON
    response = {
        "reply": f"Hi {sender}, we received your message: '{message}'",
        "app": app_package,
        "messenger": messenger,
        "groupMessage": is_group
    }
    return jsonify(response), 200  # HTTP 200 OK

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
