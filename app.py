from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import hashlib
import time
import os

app = Flask(__name__)
CORS(app)

# Параметри бази даних
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:prhFZETaRWzNFGMcYAyClmmhdinUsKYv@gondola.proxy.rlwy.net:17227/Xmara"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ======== МОДЕЛІ =========

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)
    block_until = db.Column(db.Float, default=0)  # час у секундах

# Створення таблиць
with app.app_context():
    db.create_all()

# ======== ХЕЛПЕРИ =========

def hash_password(login, password):
    return hashlib.sha256((login + password).encode()).hexdigest()

# ======== МАРШРУТИ =========

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")

@app.route("/cars", methods=["GET"])
def get_cars():
    cars = Car.query.all()
    return jsonify([{"id": car.id, "brand": car.brand, "model": car.model, "year": car.year} for car in cars])

@app.route("/cars", methods=["POST"])
def add_car():
    data = request.json
    new_car = Car(
        brand=data.get("brand"),
        model=data.get("model"),
        year=data.get("year")
    )
    db.session.add(new_car)
    db.session.commit()
    return jsonify({"id": new_car.id, "brand": new_car.brand, "model": new_car.model, "year": new_car.year}), 201

@app.route("/cars/<int:car_id>", methods=["GET"])
def get_car(car_id):
    car = Car.query.get(car_id)
    if car:
        return jsonify({"id": car.id, "brand": car.brand, "model": car.model, "year": car.year})
    return jsonify({"error": "Car not found"}), 404

@app.route("/cars/<int:car_id>", methods=["PUT"])
def update_car(car_id):
    data = request.json
    car = Car.query.get(car_id)
    if car:
        car.brand = data.get("brand")
        car.model = data.get("model")
        car.year = data.get("year")
        db.session.commit()
        return jsonify({"id": car.id, "brand": car.brand, "model": car.model, "year": car.year})
    return jsonify({"error": "Car not found"}), 404

@app.route("/cars/<int:car_id>", methods=["DELETE"])
def delete_car(car_id):
    car = Car.query.get(car_id)
    if car:
        db.session.delete(car)
        db.session.commit()
        return jsonify({"message": "Car deleted"})
    return jsonify({"error": "Car not found"}), 404

# ======== АУТЕНТИФІКАЦІЯ =========

@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    login = data.get("login")
    password = data.get("password")

    if User.query.filter_by(login=login).first():
        return jsonify({"error": "Користувач вже існує"}), 400

    user = User(login=login, password_hash=hash_password(login, password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Реєстрація успішна!"})

@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    login = data.get("login")
    password = data.get("password")
    user = User.query.filter_by(login=login).first()

    if not user:
        return jsonify({"error": "Користувача не знайдено"}), 404

    now = time.time()
    if user.block_until > now:
        remaining = int(user.block_until - now)
        return jsonify({"error": f"Заблоковано. Зачекайте {remaining} сек."}), 403

    if user.password_hash == hash_password(login, password):
        user.failed_attempts = 0
        db.session.commit()
        return jsonify({"message": "Аутентифікація пройдена!"})
    else:
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.block_until = now + 60
            user.failed_attempts = 0
            db.session.commit()
            return jsonify({"error": "Заблоковано на 60 секунд після 3 спроб"}), 403
        else:
            db.session.commit()
            return jsonify({"error": "Невірний пароль", "attempts_left": 3 - user.failed_attempts}), 401

# ======== Запуск =========

if __name__ == "__main__":
    app.run(debug=True)
