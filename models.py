from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    pets = db.relationship("Pet", backref="owner", lazy=True)

    def set_password(self, raw_password: str):
        # pbkdf2 avoids hashlib.scrypt issues 
        self.password_hash = generate_password_hash(
            raw_password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

class Pet(db.Model):
    __tablename__ = "pets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(255), default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tasks = db.relationship("Task", backref="pet", lazy=True, cascade="all, delete-orphan")
    medical_record = db.relationship("MedicalRecord", backref="pet", uselist=False, cascade="all, delete-orphan")

    def to_card(self):
        return {
            "id": self.id, "name": self.name, "type": self.type,
            "photo_path": self.photo_path or "/static/uploads/placeholder.jpg",
        }

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    desc = db.Column(db.Text, default="")
    date = db.Column(db.DateTime, default=datetime.utcnow)
    repeat = db.Column(db.String(40), default="None")
    status = db.Column(db.String(32), default="pending")

    def to_row(self):
        dt = self.date.strftime("%Y-%m-%d %H:%M") if self.date else ""
        return {
            "id": self.id, "pet_id": self.pet_id, "title": self.title,
            "desc": self.desc, "date": dt, "repeat": self.repeat, "status": self.status,
        }

class MedicalRecord(db.Model):
    __tablename__ = "medical_records"
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False, unique=True)
    vaccine = db.Column(db.Text, default="")
    allergies = db.Column(db.Text, default="")
    medication = db.Column(db.Text, default="")
    vet_info = db.Column(db.Text, default="")

    def to_view(self):
        return {
            "vaccine": self.vaccine, "allergies": self.allergies,
            "medication": self.medication, "vet_info": self.vet_info,
        }
