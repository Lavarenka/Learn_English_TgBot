"""
Настройка подключения к базе данных (SQLAlchemy).

Адрес базы берётся из переменной окружения DATABASE_URL (см. .env /
app/config.py). Если она не задана — используется локальный файл SQLite
(english_bot.db) рядом с проектом, как раньше: для обычного локального
запуска без Docker не нужно поднимать отдельный сервер БД.

В Docker (и локальном docker-compose.yml, и продакшен-варианте)
DATABASE_URL указывает на PostgreSQL — например:
    postgresql+psycopg://user:password@db:5432/english_bot
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False нужен только для SQLite, потому что и
    # FastAPI, и телеграм-бот могут обращаться к БД из разных потоков.
    # PostgreSQL это ограничение не имеет — там за это отвечает пул
    # соединений SQLAlchemy.
    _connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)


# expire_on_commit=False важен для бота: объекты Question, отобранные для
# игры (start_new_game), сохраняются в user_games на время всей партии, уже
# после того как сессия, в которой они были загружены, закрыта. Без этой
# настройки SQLAlchemy "протухал" бы их атрибуты после commit/закрытия
# сессии, и обращение к question.question/.hint/.correct кидало бы
# DetachedInstanceError.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    """Генератор сессии для использования как FastAPI-зависимость."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
