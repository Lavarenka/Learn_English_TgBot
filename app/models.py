"""
Модели SQLAlchemy: Level (уровень сложности) и Question (вопрос).

Один уровень -> много вопросов.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
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
