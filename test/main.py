from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

print("ENV VARIABLES:", os.environ)  # Cek semua env variable
print("DATABASE_URL:", os.getenv("DATABASE_URL"))  # Pastikan URL database terdeteksi

app = Flask(__name__)

# Gunakan URL PostgreSQL dari Railway
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Buat model database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Buat tabel di database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "PostgreSQL Flask API Connected!"

if __name__ == "__main__":
    app.run(debug=True)
