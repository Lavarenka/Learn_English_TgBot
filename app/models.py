"""
Модели SQLAlchemy: Level (уровень сложности), Question (вопрос) и
AdminUser (аккаунт для входа в /manage и /admin).

Один уровень -> много вопросов.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)  # тех. имя, напр. "beginner"
    name = Column(String(128), nullable=False)                          # отображаемое имя, напр. "🟢 Начальный"
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship(
        "Question", back_populates="level", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Level key={self.key!r} name={self.name!r}>"

    def __str__(self) -> str:
        # Используется SQLAdmin в выпадающих списках и ссылках (например,
        # при выборе уровня в форме вопроса) — показываем понятное имя
        # вместо технического repr().
        return self.name


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False)

    question = Column(String(255), nullable=False)   # напр. "break"
    correct = Column(String(255), nullable=False)     # варианты ответа через "/", напр. "ломать/сломать"
    hint = Column(Text, nullable=True)                 # подсказка

    level = relationship("Level", back_populates="questions")

    def correct_answers(self) -> list[str]:
        """Разбивает поле correct на список вариантов по разделителю '/'."""
        return [part.strip() for part in self.correct.split("/") if part.strip()]

    def __repr__(self) -> str:
        return f"<Question {self.question!r} level_id={self.level_id}>"

    def __str__(self) -> str:
        # Используется SQLAdmin в списке вопросов на странице деталей
        # уровня — так вместо "<Question 'break' level_id=1>" видно просто
        # "break — ломать/сломать".
        return f"{self.question} — {self.correct}"


class AdminUser(Base):
    """
    Аккаунт для входа в /manage и /admin. Пароль хранится только в виде
    хэша (см. app/auth.py) — открытый текст пароля в базе не сохраняется.
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<AdminUser username={self.username!r}>"

    def __str__(self) -> str:
        return self.username
