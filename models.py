from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    performances = db.relationship("Performance", back_populates="user")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    muscle = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.Float, nullable=False, default=1.0)

    performances = db.relationship("Performance", back_populates="exercise")


class Performance(db.Model):
    __tablename__ = "performances"

    id = db.Column(db.Integer, primary_key=True)

    weight = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)

    user = db.relationship("User", back_populates="performances")
    exercise = db.relationship("Exercise", back_populates="performances")