"""
Настройка веб-админки SQLAdmin.

Даёт полноценный интерфейс для просмотра и редактирования уровней и
вопросов: таблицы со списком, поиск, формы создания/редактирования,
удаление — без единой строчки кода со стороны пользователя.

Подключается в app/api.py и доступна по адресу /admin.
"""
from sqladmin import Admin, ModelView

from app.models import Level, Question


class LevelAdmin(ModelView, model=Level):
    name = "Уровень"
    name_plural = "Уровни"
    icon = "fa-solid fa-layer-group"

    column_list = [Level.id, Level.key, Level.name, Level.description]
    column_searchable_list = [Level.key, Level.name]
    column_sortable_list = [Level.id, Level.key, Level.name]

    form_columns = [Level.key, Level.name, Level.description]

    # Показываем количество вопросов прямо в списке уровней через related-колонку
    column_details_list = [Level.id, Level.key, Level.name, Level.description, Level.questions]


class QuestionAdmin(ModelView, model=Question):
    name = "Вопрос"
    name_plural = "Вопросы"
    icon = "fa-solid fa-circle-question"

    column_list = [Question.id, Question.level, Question.question, Question.correct, Question.hint]
    column_searchable_list = [Question.question, Question.correct]
    column_sortable_list = [Question.id, Question.question]

    form_columns = [Question.level, Question.question, Question.correct, Question.hint]
    form_ajax_refs = {
        "level": {
            "fields": ("key", "name"),
            "order_by": "key",
        }
    }


def setup_admin(app, engine):
    """Монтирует SQLAdmin поверх FastAPI-приложения. Вызывается из app/api.py."""
    admin = Admin(app, engine, title="Learn English Bot — Админка")
    admin.add_view(LevelAdmin)
    admin.add_view(QuestionAdmin)
    return admin
