import hashlib
import json
import secrets
from pathlib import Path

USERS_FILE = Path("config/users.json")
SESSION_STORE = {}


def _load_users():
    with USERS_FILE.open("r", encoding="utf-8") as users_file:
        data = json.load(users_file)
    return data.get("users", [])


def _sanitize_user(user):
    return {
        "username": user["username"],
        "name": user.get("name", user["username"]),
        "role": user["role"],
    }


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_user(username, password):
    for user in _load_users():
        if user["username"] == username and user["password_hash"] == _hash_password(password):
            return _sanitize_user(user)
    return None


def create_session(user):
    token = secrets.token_hex(24)
    SESSION_STORE[token] = user
    return token


def get_user_from_token(token):
    if not token:
        return None
    return SESSION_STORE.get(token)


def clear_session(token):
    if token in SESSION_STORE:
        del SESSION_STORE[token]
