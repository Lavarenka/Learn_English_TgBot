"""
"Блокнотный" редактор уровней — простая страница поверх FastAPI, без
отдельного фронтенда.

Идея: открываешь уровень — видишь ВСЕ его вопросы одним текстом в
привычном формате "слово | перевод | подсказка" (как раньше в .txt
файлах), правишь текст как обычный блокнот (что-то добавил, что-то
удалил, что-то поправил), жмёшь "Сохранить" — весь список вопросов
уровня в базе заменяется на то, что получилось.

Здесь же можно переименовать уровень (name/описание) и удалить его
целиком вместе со всеми словами.

Доступно по адресу /manage — отдельно от SQLAdmin (/admin), который
остаётся для точечного редактирования/удаления одной записи.

Весь раздел защищён авторизацией (см. app/auth.py) — без входа в систему
доступна только страница логина.
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    authenticate,
    create_session_cookie_value,
    read_session_cookie_value,
)

router = APIRouter(prefix="/manage", tags=["manage"])


PAGE_STYLE = """
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 900px;
         margin: 40px auto; padding: 0 20px; color: #1a1a1a; background: #fafafa; }
  h1 { font-size: 22px; }
  h2 { font-size: 18px; color: #444; font-weight: normal; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .level-list { list-style: none; padding: 0; }
  .level-list li { background: white; border: 1px solid #e5e5e5; border-radius: 8px;
                    padding: 14px 18px; margin-bottom: 10px; display: flex;
                    justify-content: space-between; align-items: center; gap: 10px; }
  .level-list .meta { color: #888; font-size: 13px; }
  .level-list .actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
  textarea { width: 100%; height: 60vh; font-family: 'Consolas', 'Menlo', monospace;
             font-size: 14px; padding: 12px; border: 1px solid #ccc; border-radius: 8px;
             box-sizing: border-box; line-height: 1.5; }
  input[type=text], input[type=password] { padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px;
                      font-size: 14px; width: 300px; box-sizing: border-box; }
  button, .btn { background: #2563eb; color: white; border: none; padding: 10px 18px;
                 border-radius: 6px; font-size: 14px; cursor: pointer; display: inline-block; }
  button:hover, .btn:hover { background: #1d4ed8; text-decoration: none; }
  .btn-secondary { background: #6b7280; }
  .btn-secondary:hover { background: #4b5563; }
  .btn-danger { background: #dc2626; padding: 8px 14px; font-size: 13px; }
  .btn-danger:hover { background: #b91c1c; }
  .btn-small { padding: 8px 14px; font-size: 13px; }
  .hint { color: #666; font-size: 13px; margin: 8px 0 16px; }
  .toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; }
  .warning { background: #fef3cd; border: 1px solid #f0d264; border-radius: 6px;
             padding: 10px 14px; font-size: 13px; margin: 12px 0; }
  .error { background: #fee2e2; border: 1px solid #f87171; border-radius: 6px;
           padding: 10px 14px; font-size: 13px; margin: 12px 0; }
  .back { display: inline-block; margin-bottom: 20px; }
  form.inline { display: inline; }
  .rename-form { display: flex; gap: 8px; margin: 10px 0 0; }
  .topbar { display: flex; justify-content: space-between; align-items: center; }
  .topbar .user { color: #666; font-size: 13px; }
  .login-box { max-width: 360px; margin: 80px auto; background: white; border: 1px solid #e5e5e5;
               border-radius: 10px; padding: 28px; }
  .login-box input { width: 100%; margin-bottom: 12px; }
  .login-box button { width: 100%; }
</style>
"""


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------

def get_current_username(request: Request) -> str | None:
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_value:
        return None
    return read_session_cookie_value(cookie_value)


def require_login(request: Request):
    """FastAPI-зависимость: редиректит на /manage/login, если не залогинен.

    Кидает RedirectResponse через исключение неудобно в FastAPI, поэтому
    вместо этого возвращаем username или None, и каждый роут сам решает,
    что делать — см. _redirect_if_anonymous ниже для страниц, и обычную
    проверку для API-подобных POST-эндпоинтов.
    """
    return get_current_username(request)


def _redirect_if_anonymous(username: str | None):
    if not username:
        return RedirectResponse("/manage/login", status_code=303)
    return None


@router.get("/login", response_class=HTMLResponse)
def login_page(error: int = 0):
    error_banner = (
        '<div class="error">Неверный логин или пароль</div>' if error else ""
    )
    html = f"""
    <html><head><title>Вход — Learn English Bot</title>{PAGE_STYLE}</head>
    <body>
      <div class="login-box">
        <h1>🔐 Вход в админку</h1>
        {error_banner}
        <form action="/manage/login" method="post">
          <input type="text" name="username" placeholder="Логин" required autofocus>
          <input type="password" name="password" placeholder="Пароль" required>
          <button type="submit">Войти</button>
        </form>
      </div>
    </body></html>
    """
    return html


@router.post("/login")
def do_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate(db, username, password)
    if not user:
        return RedirectResponse("/manage/login?error=1", status_code=303)

    response = RedirectResponse("/manage/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_cookie_value(user.username),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/logout")
def do_logout():
    response = RedirectResponse("/manage/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Страницы управления (защищены авторизацией)
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def manage_home(username: str | None = Depends(require_login), db: Session = Depends(get_db)):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    levels = crud.get_levels(db)

    rows = ""
    for lv in levels:
        count = crud.count_questions(db, lv.id)
        rows += f"""
        <li>
          <div>
            <a href="/manage/levels/{lv.id}"><strong>{lv.name}</strong></a>
            <div class="meta">key: {lv.key} · {count} слов</div>
          </div>
          <div class="actions">
            <a href="/manage/levels/{lv.id}" class="btn btn-small">Список слов</a>
            <a href="/manage/levels/{lv.id}/edit" class="btn btn-secondary btn-small">Переименовать</a>
            <form action="/manage/levels/{lv.id}/delete" method="post" class="inline"
                  onsubmit="return confirm('Удалить уровень «{lv.name}» и все {count} слов в нём? Это необратимо.');">
              <button type="submit" class="btn-danger">Удалить</button>
            </form>
          </div>
        </li>
        """

    html = f"""
    <html><head><title>Learn English Bot — Управление словами</title>{PAGE_STYLE}</head>
    <body>
      <div class="topbar">
        <h1>📚 Управление уровнями и словами</h1>
        <div class="user">{username} · <a href="/manage/logout">Выйти</a></div>
      </div>
      <p class="hint">
        Открой уровень, чтобы увидеть и отредактировать весь список слов одним текстом —
        как раньше в блокноте. Для тонкой правки одной записи можно использовать
        <a href="/admin">обычную админку</a>.
      </p>

      <div class="toolbar">
        <form action="/manage/levels/create" method="post" class="inline" style="display:flex; gap:10px;">
          <input type="text" name="key" placeholder="key (латиницей, напр. food)" required>
          <input type="text" name="name" placeholder="Название (напр. 🍎 Еда)" required>
          <button type="submit">+ Новый уровень</button>
        </form>
      </div>

      <ul class="level-list">{rows}</ul>
    </body></html>
    """
    return html


@router.post("/levels/create")
def create_level(
    username: str | None = Depends(require_login),
    key: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    if not crud.get_level_by_key(db, key):
        level = crud.create_level(db, key=key, name=name)
        return RedirectResponse(f"/manage/levels/{level.id}", status_code=303)
    return RedirectResponse("/manage/?error=level_exists", status_code=303)


@router.get("/levels/{level_id}/edit", response_class=HTMLResponse)
def edit_level_form(level_id: int, username: str | None = Depends(require_login), db: Session = Depends(get_db)):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    level = crud.get_level_by_id(db, level_id)
    if not level:
        return HTMLResponse("<p>Уровень не найден. <a href='/manage/'>Назад</a></p>", status_code=404)

    html = f"""
    <html><head><title>Переименовать {level.name}</title>{PAGE_STYLE}</head>
    <body>
      <a href="/manage/" class="back">← Ко всем уровням</a>
      <h1>Переименовать уровень</h1>
      <p class="hint">key: {level.key} (техническое имя уровня не меняется)</p>

      <form action="/manage/levels/{level_id}/edit" method="post" class="rename-form" style="flex-direction:column; align-items:flex-start;">
        <input type="text" name="name" value="{level.name}" placeholder="Название" required style="width:100%;">
        <input type="text" name="description" value="{level.description or ''}" placeholder="Описание" style="width:100%;">
        <div class="toolbar" style="margin-top:10px;">
          <button type="submit">💾 Сохранить</button>
          <a href="/manage/" class="btn btn-secondary">Отмена</a>
        </div>
      </form>
    </body></html>
    """
    return html


@router.post("/levels/{level_id}/edit")
def edit_level_submit(
    level_id: int,
    username: str | None = Depends(require_login),
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    level = crud.get_level_by_id(db, level_id)
    if not level:
        return HTMLResponse("<p>Уровень не найден.</p>", status_code=404)

    crud.update_level(db, level, name=name, description=description)
    return RedirectResponse("/manage/", status_code=303)


@router.post("/levels/{level_id}/delete")
def delete_level_submit(level_id: int, username: str | None = Depends(require_login), db: Session = Depends(get_db)):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    level = crud.get_level_by_id(db, level_id)
    if level:
        crud.delete_level(db, level)
    return RedirectResponse("/manage/", status_code=303)


@router.get("/levels/{level_id}", response_class=HTMLResponse)
def edit_level(level_id: int, username: str | None = Depends(require_login), saved: int = 0, db: Session = Depends(get_db)):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    level = crud.get_level_by_id(db, level_id)
    if not level:
        return HTMLResponse("<p>Уровень не найден. <a href='/manage/'>Назад</a></p>", status_code=404)

    text = crud.questions_to_text(db, level_id)
    count = crud.count_questions(db, level_id)

    saved_banner = (
        '<div class="warning" style="background:#d1fae5; border-color:#34d399;">✅ Сохранено</div>'
        if saved else ""
    )

    html = f"""
    <html><head><title>{level.name} — редактирование слов</title>{PAGE_STYLE}</head>
    <body>
      <a href="/manage/" class="back">← Ко всем уровням</a>
      <h1>{level.name}</h1>
      <h2>key: {level.key} · сейчас {count} слов</h2>
      {saved_banner}

      <p class="hint">
        Одна строка — одно слово, формат: <code>слово | перевод | подсказка</code>
        (перевод можно указать несколько вариантов через <code>/</code>).
        Просто отредактируй текст ниже как обычный блокнот и нажми «Сохранить» —
        весь список слов этого уровня в базе будет заменён на то, что здесь написано.
      </p>

      <form action="/manage/levels/{level_id}/save" method="post">
        <textarea name="text" spellcheck="false">{text}</textarea>
        <div class="toolbar" style="margin-top:14px;">
          <button type="submit">💾 Сохранить</button>
          <a href="/manage/" class="btn btn-secondary">Отмена</a>
        </div>
      </form>
    </body></html>
    """
    return html


@router.post("/levels/{level_id}/save")
def save_level(level_id: int, username: str | None = Depends(require_login), text: str = Form(...), db: Session = Depends(get_db)):
    redirect = _redirect_if_anonymous(username)
    if redirect:
        return redirect

    level = crud.get_level_by_id(db, level_id)
    if not level:
        return HTMLResponse("<p>Уровень не найден.</p>", status_code=404)

    crud.bulk_add_questions_from_text(db, level_id, text, replace_existing=True)
    return RedirectResponse(f"/manage/levels/{level_id}?saved=1", status_code=303)
