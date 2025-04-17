import psycopg2
import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/data", methods=["POST"])
def add_or_update_data():
    data = request.json
    name = data.get("name")
    value = data.get("value")

    if not name or value is None:
        return jsonify({"error": "Field 'name' and 'value' are required"}), 400

    if isinstance(value, (dict, list)):  
        value_json = json.dumps(value)
    else:
        value_json = value

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM data WHERE name = %s", (name,))
    existing = cur.fetchone()

    if existing:
        cur.execute("UPDATE data SET value = %s WHERE name = %s", (value_json, name))
    else:
        cur.execute("INSERT INTO data (name, value) VALUES (%s, %s)", (name, value_json))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Data saved", "name": name, "value": value})


@app.route("/data/<name>", methods=["GET"])
def get_data(name):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT value FROM data WHERE name = %s", (name,))
    data = cur.fetchone()

    cur.close()
    conn.close()

    if not data:
        return jsonify({"error": "Data not found"}), 404

    value = data[0]

    try:
        value = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        pass

    return jsonify({"name": name, "value": value})

def RecaptchaV3():
    import requests
    ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=ahgyd1gkfkhe'
    url_base = 'https://www.google.com/recaptcha/'
    post_data = "v={}&reason=q&c={}&k={}&co={}"
    client = requests.Session()
    client.headers.update({'content-type': 'application/x-www-form-urlencoded'})

    matches = re.findall(r'([api2|enterprise]+)/anchor\?(.*)', ANCHOR_URL)[0]
    url_base += matches[0] + '/'
    params = matches[1]
    res = client.get(url_base + 'anchor', params=params)

    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    params = dict(pair.split('=') for pair in params.split('&'))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])

    res = client.post(url_base + 'reload', params=f'k={params["k"]}', data=post_data)
    answer = re.findall(r'"rresp","(.*?)"', res.text)[0]
    return answer

def ouo_bypass(url):
    client = requests.Session()
    client.headers.update({
        'authority': 'ouo.io',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'referer': 'http://www.google.com/ig/adde?moduleurl=',
        'upgrade-insecure-requests': '1',
    })

    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    id = tempurl.split('/')[-1]
    res = client.get(tempurl, impersonate="chrome110")
    next_url = f"{p.scheme}://{p.hostname}/go/{id}"

    for _ in range(2):
        if res.headers.get('Location'):
            break

        bs4 = BeautifulSoup(res.content, 'lxml')
        inputs = bs4.form.find_all("input", {"name": re.compile(r"token$")})
        data = {input.get('name'): input.get('value') for input in inputs}
        data['x-token'] = RecaptchaV3()

        h = {'content-type': 'application/x-www-form-urlencoded'}

        res = client.post(next_url, data=data, headers=h, 
            allow_redirects=False, impersonate="chrome110")
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"

    return {
        'original_link': url,
        'bypassed_link': res.headers.get('Location')
    }

@app.route('/bypass', methods=['POST'])
def bypass_api():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL'}), 400

        result = ouo_bypass(data['url'])
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def scrape_androidadult(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Gagal mengambil halaman (status {response.status_code})"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Mencari elemen <input> dengan name tertentu
    apk_file = soup.find("input", {"name": "getpostidapkfile"})
    mirror_apk = soup.find("input", {"name": "getpostidmirrorapk"})

    if apk_file and apk_file["value"] == "":
        apk_file = soup.find("input", {"name": "getpostidmod_apk"})
    if mirror_apk and mirror_apk["value"] == "":
        mirror_apk = soup.find("input", {"name": "getpostidmirrormodapk"})
    
    apk_url = apk_file["value"] if apk_file else None
    mirror_url = mirror_apk["value"] if mirror_apk else None

    return {
        "APK File": apk_url,
        "Mirror APK": mirror_url
    }

@app.route("/androidadult", methods=["POST"])
def scrape_api():
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "URL diperlukan"}), 400

        result = scrape_androidadult(data["url"])
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
