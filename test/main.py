import psycopg2
import os
import re
from flask import Flask, request, jsonify
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/data", methods=["POST"])
def add_or_update_data():
    data = request.json
    name = data.get("name")
    value = data.get("value")

    if not name or not value:
        return jsonify({"error": "Field 'name' and 'value' are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM data WHERE name = %s", (name,))
    existing = cur.fetchone()

    if existing:
        cur.execute("UPDATE data SET value = %s WHERE name = %s", (value, name))
    else:
        cur.execute("INSERT INTO data (name, value) VALUES (%s, %s)", (name, value))

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

    if data:
        return jsonify({"name": name, "value": data[0]})
    return jsonify({"error": "Data not found"}), 404

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


if __name__ == "__main__":
    app.run(debug=True)
