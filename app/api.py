"""
FastAPI-приложение для управления уровнями и вопросами викторины.

Запуск (из корня проекта):
    uvicorn app.api:app --reload

После запуска доступны два интерфейса:
  - http://127.0.0.1:8000/admin — удобная веб-админка (SQLAdmin): таблицы,
    формы добавления/редактирования, поиск. Рекомендуется для повседневной
    работы с уровнями и вопросами.
  - http://127.0.0.1:8000/docs — интерактивная документация API (Swagger),
    там же есть отдельный эндпоинт для вставки текста с вопросами одним
    куском (bulk), как раньше вписывали в блокнот.
"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import crud, schemas
from app.admin import setup_admin

# Создаём таблицы при первом запуске, если их ещё нет.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Learn English Bot — Admin API",
    description="Управление уровнями сложности и вопросами викторины для телеграм-бота",
    version="1.0.0",
)

setup_admin(app, engine)


def _level_out(level, db: Session) -> schemas.LevelOut:
    data = schemas.LevelOut.model_validate(level)
    data.questions_count = crud.count_questions(db, level.id)
    return data


@app.get("/levels", response_model=list[schemas.LevelOut], tags=["levels"])
def list_levels(db: Session = Depends(get_db)):
    """Список всех уровней сложности с количеством вопросов в каждом."""
    return [_level_out(lv, db) for lv in crud.get_levels(db)]


@app.post("/levels", response_model=schemas.LevelOut, status_code=201, tags=["levels"])
def create_level(payload: schemas.LevelCreate, db: Session = Depends(get_db)):
    """Создать новый уровень (это и есть 'новый файл' в терминах старого проекта)."""
    if crud.get_level_by_key(db, payload.key):
        raise HTTPException(400, f"Уровень с key='{payload.key}' уже существует")
    level = crud.create_level(db, key=payload.key, name=payload.name, description=payload.description)
    return _level_out(level, db)


@app.get("/levels/{level_id}", response_model=schemas.LevelOut, tags=["levels"])
def get_level(level_id: int, db: Session = Depends(get_db)):
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    return _level_out(level, db)


@app.patch("/levels/{level_id}", response_model=schemas.LevelOut, tags=["levels"])
def update_level(level_id: int, payload: schemas.LevelUpdate, db: Session = Depends(get_db)):
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    level = crud.update_level(db, level, payload.name, payload.description)
    return _level_out(level, db)


@app.delete("/levels/{level_id}", status_code=204, tags=["levels"])
def delete_level(level_id: int, db: Session = Depends(get_db)):
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    crud.delete_level(db, level)


@app.get("/levels/{level_id}/questions", response_model=list[schemas.QuestionOut], tags=["questions"])
def list_questions(level_id: int, db: Session = Depends(get_db)):
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    return crud.get_questions(db, level_id)


@app.post("/levels/{level_id}/questions", response_model=schemas.QuestionOut, status_code=201, tags=["questions"])
def add_question(level_id: int, payload: schemas.QuestionCreate, db: Session = Depends(get_db)):
    """Добавить один вопрос вручную."""
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    return crud.add_question(db, level_id, payload.question, payload.correct, payload.hint)


@app.post(
    "/levels/{level_id}/questions/bulk",
    response_model=schemas.BulkQuestionsOut,
    tags=["questions"],
)
def add_questions_bulk(level_id: int, payload: schemas.BulkQuestionsIn, db: Session = Depends(get_db)):
    """
    Добавить сразу много вопросов текстом — как раньше вписывали в блокнот.

    Формат (одна строка = один вопрос):
        слово | перевод1/перевод2 | подсказка

    Пример:
        break | ломать/сломать | to break the rules
        speak | говорить | to speak English
    """
    level = crud.get_level_by_id(db, level_id)
    if not level:
        raise HTTPException(404, "Уровень не найден")
    added, skipped = crud.bulk_add_questions_from_text(
        db, level_id, payload.text, payload.replace_existing
    )
    return schemas.BulkQuestionsOut(added=added, skipped_lines=skipped)


@app.delete("/questions/{question_id}", status_code=204, tags=["questions"])
def delete_question(question_id: int, db: Session = Depends(get_db)):
    from app.models import Question

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(404, "Вопрос не найден")
    crud.delete_question(db, question)


@app.get("/", tags=["meta"])
def root():
    return {
        "message": "Learn English Bot Admin API",
        "admin": "/admin — удобная веб-админка для уровней и вопросов",
        "docs": "/docs — интерактивная документация API, там же bulk-добавление вопросов текстом",
    }
