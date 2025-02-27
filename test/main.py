from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Ambil DATABASE_URL dari environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")

# Koneksi ke PostgreSQL
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# **POST /data** → Menyimpan atau memperbarui data
@app.route("/data", methods=["POST"])
def add_or_update_data():
    data = request.json
    name = data.get("name")
    value = data.get("value")

    if not name or not value:
        return jsonify({"error": "Field 'name' and 'value' are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Periksa apakah data sudah ada
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

# **GET /data/<name>** → Mengambil data berdasarkan name
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

if __name__ == "__main__":
    app.run(debug=True)
