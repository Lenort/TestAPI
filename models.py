from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = 'lead'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(32), nullable=False)
    fio = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    direction = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
