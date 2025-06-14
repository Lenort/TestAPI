from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'lead'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(64), nullable=False)
    fio = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(255), nullable=False)  # заменил direction на event_type
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
