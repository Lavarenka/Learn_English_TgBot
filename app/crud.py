"""Функции для работы с БД — используются и FastAPI, и телеграм-ботом."""
import random

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Level, Question
from app.parser import parse_questions_text


def get_levels(db: Session) -> list[Level]:
    return db.query(Level).order_by(Level.id).all()


def get_level_by_key(db: Session, key: str) -> Level | None:
    return db.query(Level).filter(Level.key == key).first()


def get_level_by_id(db: Session, level_id: int) -> Level | None:
    return db.query(Level).filter(Level.id == level_id).first()


def count_questions(db: Session, level_id: int) -> int:
    return db.query(func.count(Question.id)).filter(Question.level_id == level_id).scalar() or 0


def create_level(db: Session, key: str, name: str, description: str | None = None) -> Level:
    level = Level(key=key, name=name, description=description)
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def update_level(db: Session, level: Level, name: str | None, description: str | None) -> Level:
    if name is not None:
        level.name = name
    if description is not None:
        level.description = description
    db.commit()
    db.refresh(level)
    return level


def delete_level(db: Session, level: Level) -> None:
    db.delete(level)
    db.commit()


def get_questions(db: Session, level_id: int) -> list[Question]:
    return db.query(Question).filter(Question.level_id == level_id).all()


def get_random_questions(db: Session, level_id: int, count: int) -> list[Question]:
    """Случайная выборка `count` вопросов уровня без повторений."""
    all_questions = get_questions(db, level_id)
    if count >= len(all_questions):
        random.shuffle(all_questions)
        return all_questions
    return random.sample(all_questions, count)


def get_random_questions_mixed(db: Session, count: int) -> list[Question]:
    """Случайная выборка вопросов из ВСЕХ уровней сразу (режим 'mixed')."""
    all_questions = db.query(Question).all()
    if count >= len(all_questions):
        random.shuffle(all_questions)
        return all_questions
    return random.sample(all_questions, count)


def add_question(db: Session, level_id: int, question: str, correct: str, hint: str | None) -> Question:
    q = Question(level_id=level_id, question=question, correct=correct, hint=hint or "")
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def delete_question(db: Session, question: Question) -> None:
    db.delete(question)
    db.commit()


def questions_to_text(db: Session, level_id: int) -> str:
    """
    Обратное превращение вопросов уровня в текст формата блокнота —
    для показа в textarea редактора уровня.
    """
    questions = get_questions(db, level_id)
    lines = [f"{q.question} | {q.correct} | {q.hint}" for q in questions]
    return "\n".join(lines)


def bulk_add_questions_from_text(
    db: Session, level_id: int, text: str, replace_existing: bool = False
) -> tuple[int, list[str]]:
    """
    Разбирает текст в формате блокнота ('слово | ответ | подсказка' построчно)
    и добавляет вопросы уровню level_id.

    Возвращает (сколько добавлено, список пропущенных строк с описанием ошибки).
    """
    result = parse_questions_text(text)

    if replace_existing:
        db.query(Question).filter(Question.level_id == level_id).delete()

    for pq in result.questions:
        db.add(Question(level_id=level_id, question=pq.question, correct=pq.correct, hint=pq.hint))

    db.commit()

    skipped_descriptions = [
        f"строка {num}: «{content}» — недостаточно данных (нужно минимум 2 разделителя '|')"
        for num, content in result.skipped_lines
    ]

    return len(result.questions), skipped_descriptions
