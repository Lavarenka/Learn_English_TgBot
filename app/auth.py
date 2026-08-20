"""
Авторизация для /manage и /admin.

Подход: аккаунты (логин + хэш пароля) хранятся в таблице admin_users,
после успешного входа выдаётся подписанная (itsdangerous) cookie-сессия —
без внешних библиотек авторизации и без сторонних сервисов, всё локально.

Секретный ключ для подписи cookie берётся из переменной окружения
SECRET_KEY, если она задана, иначе генерируется один раз и сохраняется в
файл .secret_key рядом с проектом — так сессии не будут "слетать" при
каждом перезапуске сервера, но при этом не нужно ничего явно настраивать
для локальной разработки.
"""
import os
import secrets
from pathlib import Path

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import Session

from app.models import AdminUser

SESSION_COOKIE_NAME = "admin_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 14  # 14 дней

_SECRET_KEY_FILE = Path(__file__).resolve().parent.parent / ".secret_key"


def _load_or_create_secret_key() -> str:
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    if _SECRET_KEY_FILE.exists():
        return _SECRET_KEY_FILE.read_text(encoding="utf-8").strip()

    key = secrets.token_hex(32)
    _SECRET_KEY_FILE.write_text(key, encoding="utf-8")
    return key


SECRET_KEY = _load_or_create_secret_key()
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="admin-session")


def hash_password(password: str) -> str:
    # bcrypt ограничивает длину пароля 72 байтами — обрезаем на всякий
    # случай, чтобы очень длинный пароль не вызывал ошибку.
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        # повреждённый/несовместимый хэш в базе
        return False


def authenticate(db: Session, username: str, password: str) -> AdminUser | None:
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session_cookie_value(username: str) -> str:
    return _serializer.dumps({"username": username})


def read_session_cookie_value(value: str) -> str | None:
    """Возвращает username из подписанной cookie, либо None если она
    отсутствует, повреждена или истёк срок действия."""
    try:
        data = _serializer.loads(value, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("username")
