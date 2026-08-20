"""
Настройка подключения к базе данных (SQLAlchemy).

Используется локальный файл SQLite (english_bot.db), который лежит рядом
с проектом — никакого отдельного сервера БД устанавливать не нужно.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./english_bot.db"

# check_same_thread=False нужен, потому что и FastAPI, и телеграм-бот
# могут обращаться к SQLite из разных потоков.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)


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
