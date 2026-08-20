"""Pydantic-схемы для FastAPI (запросы/ответы)."""
from pydantic import BaseModel, Field, ConfigDict


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    correct: str
    hint: str | None = None


class QuestionCreate(BaseModel):
    question: str
    correct: str
    hint: str | None = None


class LevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    description: str | None = None
    questions_count: int = 0


class LevelCreate(BaseModel):
    key: str = Field(..., description="Техническое имя уровня, напр. 'beginner'")
    name: str = Field(..., description="Отображаемое имя, напр. '🟢 Начальный'")
    description: str | None = None


class LevelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class BulkQuestionsIn(BaseModel):
    """Текст в формате блокнота: 'слово | ответ1/ответ2 | подсказка' построчно."""
    text: str
    replace_existing: bool = Field(
        default=False,
        description="Если true — сначала удалить все текущие вопросы уровня, затем добавить новые",
    )


class BulkQuestionsOut(BaseModel):
    added: int
    skipped_lines: list[str]
