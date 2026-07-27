"""
Database models.

User  -> a registered account. Passwords are never stored in plain text;
         they are hashed with bcrypt and only the hash is persisted.
Note  -> a single note "owned" by a user (the resource for this lab).
"""
from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from config import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    # One user has many notes; deleting a user deletes their notes too.
    notes = db.relationship(
        "Note", backref="user", cascade="all, delete-orphan", lazy=True
    )

    # --- password handling --------------------------------------------
    # password_hash is write-only: you can assign a plain-text password to
    # it (user.password_hash = "secret") and it will be hashed and stored,
    # but reading it back raises an error so the plain hash is never
    # accidentally exposed (e.g. in a to_dict()).
    @hybrid_property
    def password_hash(self):
        raise AttributeError("password_hash is not a readable attribute")

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode("utf-8"))
        self._password_hash = password_hash.decode("utf-8")

    def authenticate(self, password):
        """Return True if the given plain-text password matches the hash."""
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))

    # --- validations -----------------------------------------------------
    @validates("username")
    def validate_username(self, key, username):
        if not username or not username.strip():
            raise ValueError("Username must be present")
        return username

    def to_dict(self):
        return {"id": self.id, "username": self.username}

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    @validates("title")
    def validate_title(self, key, title):
        if not title or not title.strip():
            raise ValueError("Title must be present")
        return title

    @validates("content")
    def validate_content(self, key, content):
        if not content or not content.strip():
            raise ValueError("Content must be present")
        return content

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Note {self.id}: {self.title}>"
