"""
Настройка веб-админки SQLAdmin.

Даёт полноценный интерфейс для просмотра и редактирования уровней и
вопросов: таблицы со списком, поиск, формы создания/редактирования,
удаление — без единой строчки кода со стороны пользователя.

Подключается в app/api.py и доступна по адресу /admin. Защищена той же
авторизацией (аккаунты в таблице admin_users), что и /manage — вход через
SQLAdmin использует ту же функцию authenticate() из app/auth.py.
"""
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.database import SessionLocal
from app.models import Level, Question
from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    authenticate,
    create_session_cookie_value,
    read_session_cookie_value,
)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        db = SessionLocal()
        try:
            user = authenticate(db, username, password)
        finally:
            db.close()

        if not user:
            return False

        request.session.update({"sqladmin_username": user.username})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # SQLAdmin по умолчанию использует SessionMiddleware (подписанные
        # cookie через starlette), это отдельный механизм от cookie
        # /manage, но использует тот же самый набор логин/пароль из БД.
        return bool(request.session.get("sqladmin_username"))


class LevelAdmin(ModelView, model=Level):
    name = "Уровень"
    name_plural = "Уровни"
    icon = "fa-solid fa-layer-group"

    column_list = [Level.id, Level.key, Level.name, Level.description]
    column_searchable_list = [Level.key, Level.name]
    column_sortable_list = [Level.id, Level.key, Level.name]

    form_columns = [Level.key, Level.name, Level.description]

    # На странице деталей уровня показываем полный список его вопросов —
    # кликаешь на уровень в списке и сразу видишь все слова внутри него.
    column_details_list = [Level.id, Level.key, Level.name, Level.description, Level.questions]


class QuestionAdmin(ModelView, model=Question):
    name = "Вопрос"
    name_plural = "Вопросы"
    icon = "fa-solid fa-circle-question"

    # Показываем сразу много вопросов на одной странице списка (по
    # умолчанию у SQLAdmin 10 на страницу — этого мало, когда в уровне
    # 30-40+ слов и хочется видеть их одним взглядом).
    page_size = 100
    page_size_options = [50, 100, 200, 500]

    column_list = [Question.id, Question.level, Question.question, Question.correct, Question.hint]
    column_searchable_list = [Question.question, Question.correct]
    column_sortable_list = [Question.id, Question.question, Question.level_id]

    # Фильтр по уровню — можно быстро отсеять список до одного уровня,
    # не листая все вопросы подряд.
    column_filters = [Question.level_id]

    form_columns = [Question.level, Question.question, Question.correct, Question.hint]
    form_ajax_refs = {
        "level": {
            "fields": ("key", "name"),
            "order_by": "key",
        }
    }


def setup_admin(app, engine):
    """Монтирует SQLAdmin поверх FastAPI-приложения. Вызывается из app/api.py."""
    from app.auth import SECRET_KEY

    admin = Admin(
        app,
        engine,
        title="Learn English Bot — Админка",
        authentication_backend=AdminAuth(secret_key=SECRET_KEY),
    )
    admin.add_view(LevelAdmin)
    admin.add_view(QuestionAdmin)
    return admin
