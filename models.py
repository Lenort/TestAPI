from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'lead'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(64), nullable=False)       # увеличил длину для безопасного хранения
    fio = db.Column(db.String(255), nullable=False)           # увеличил длину, чтобы вместить длинные имена
    phone = db.Column(db.String(50), nullable=False)          # увеличил длину для международных форматов
    city = db.Column(db.String(100), nullable=False)          # увеличил длину
    direction = db.Column(db.String(255), nullable=False)     # увеличил длину
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
