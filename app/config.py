"""
Настройки проекта — токен бота и секретный ключ сессий читаются из
переменных окружения (файл .env в корне проекта), а не хранятся в коде.

Это важно перед деплоем в продакшен: .env никогда не попадает в git
(он в .gitignore) и не хранится внутри Docker-образа — только
подключается к контейнеру снаружи при запуске.

Приоритет для BOT_TOKEN (для плавного перехода со старой схемы):
  1. Переменная окружения BOT_TOKEN / .env
  2. Старый файл key.py (BOT_TOKEN = '...') — для обратной совместимости,
     если .env ещё не настроен

Если не найдено ни то, ни другое — приложение не запустится с понятной
ошибкой, а не будет падать позже с непонятным исключением от Telegram.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Подхватываем .env, если он есть — переменные окружения, заданные явно
# (например, при запуске в Docker через docker-compose), имеют приоритет
# и не перезаписываются файлом (override=False - поведение по умолчанию).
load_dotenv(PROJECT_ROOT / ".env")


def _get_bot_token() -> str:
    token = os.environ.get("BOT_TOKEN")
    if token:
        return token

    # Обратная совместимость со старой схемой хранения токена в key.py
    try:
        from key import BOT_TOKEN as legacy_token
        if legacy_token:
            return legacy_token
    except ImportError:
        pass

    raise RuntimeError(
        "BOT_TOKEN не найден. Задай его в файле .env в корне проекта:\n"
        "  BOT_TOKEN=твой_токен_от_BotFather\n"
        "(см. .env.example)"
    )


BOT_TOKEN = _get_bot_token()
