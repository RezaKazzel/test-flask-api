import psycopg2
import os
import re
import math
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ================== LEVEL ==================
@app.route('/level', methods=['POST'])
def result():
    data = request.get_json()
    level = int(data.get("level", 1))
    tujuan = int(data.get("tujuan", level))

    ayam = 0
    for i in range(level, tujuan + 1):
        bebek = math.floor(1.5 * (i ** 1.5) + 10)
        ayam += bebek

    return jsonify({"result": ayam})

# ================== STREAK ==================
def streak_to_time(streak):
    total_seconds = streak * 210

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if days > 0: parts.append(f"{days} Hari")
    if hours > 0: parts.append(f"{hours} Jam")
    if minutes > 0: parts.append(f"{minutes} Menit")
    if seconds > 0: parts.append(f"{seconds} Detik")

    return " ".join(parts)

@app.route("/streak", methods=["GET"])
def streak():
    streak_param = request.args.get("streak")

    if streak_param is None:
        return jsonify({"error": "Missing 'streak' parameter"}), 400

    try:
        streak_count = int(streak_param)
        if streak_count < 0:
            raise ValueError
    except:
        return jsonify({"error": "Invalid streak"}), 400

    return jsonify({
        "streak": streak_count,
        "time": streak_to_time(streak_count)
    })

# ================== DATABASE ==================
@app.route("/data", methods=["POST"])
def add_or_update_data():
    data = request.json
    name = data.get("name")
    value = data.get("value")

    if not name or value is None:
        return jsonify({"error": "name & value required"}), 400

    if isinstance(value, (dict, list)):
        value = json.dumps(value)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM data WHERE name=%s", (name,))
    existing = cur.fetchone()

    if existing:
        cur.execute("UPDATE data SET value=%s WHERE name=%s", (value, name))
    else:
        cur.execute("INSERT INTO data (name,value) VALUES (%s,%s)", (name, value))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "ok"})

@app.route("/data/<name>", methods=["GET"])
def get_data(name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM data WHERE name=%s", (name,))
    data = cur.fetchone()

    cur.close()
    conn.close()

    if not data:
        return jsonify({"error": "not found"}), 404

    value = data[0]

    try:
        value = json.loads(value)
    except:
        pass

    return jsonify({"name": name, "value": value})

# ================== RECAPTCHA ==================
def RecaptchaV3():
    client = requests.Session()

    ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=x'

    res = client.get(ANCHOR_URL)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]

    data = {
        "v": "pCoGBhjs9s8EhFOHJFe8cqis",
        "reason": "q",
        "c": token,
        "k": "6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x",
        "co": "aHR0cHM6Ly9vdW8ucHJlc3M6NDQz"
    }

    res = client.post("https://www.google.com/recaptcha/api2/reload?k=" + data["k"], data=data)
    return re.findall(r'"rresp","(.*?)"', res.text)[0]

# ================== OUO BYPASS ==================
def ouo_bypass(url):
    client = requests.Session()

    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    _id = tempurl.split('/')[-1]

    res = client.get(tempurl, impersonate="chrome110")
    next_url = f"{p.scheme}://{p.hostname}/go/{_id}"

    for _ in range(2):
        if res.headers.get("Location"):
            break

        soup = BeautifulSoup(res.text, "lxml")
        inputs = soup.find_all("input")

        data = {i.get("name"): i.get("value") for i in inputs if i.get("name")}
        data["x-token"] = RecaptchaV3()

        res = client.post(next_url, data=data, allow_redirects=False, impersonate="chrome110")
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{_id}"

    return {
        "original": url,
        "bypassed": res.headers.get("Location")
    }

@app.route("/bypass", methods=["POST"])
def bypass_api():
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "url required"}), 400

        return jsonify(ouo_bypass(data["url"]))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================== SCRAPER ==================
@app.route("/androidadult", methods=["POST"])
def scrape_api():
    try:
        data = request.get_json()
        url = data.get("url")

        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        apk = soup.find("input", {"name": "getpostidapkfile"})
        mirror = soup.find("input", {"name": "getpostidmirrorapk"})

        return jsonify({
            "apk": apk["value"] if apk else None,
            "mirror": mirror["value"] if mirror else None
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
