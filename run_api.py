"""Запуск Admin API. Из корня проекта: python run_api.py"""
import os

import uvicorn

if __name__ == "__main__":
    # HOST=127.0.0.1 — для обычного локального запуска на своей машине,
    # HOST=0.0.0.0 — обязательно внутри Docker, иначе снаружи контейнера
    # (в том числе через nginx) до сервиса не достучаться.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    # reload=True удобен для локальной разработки (автоперезапуск при
    # изменении файлов), но не нужен и не должен использоваться в
    # продакшене — там код не меняется на лету и обычно нет смонтированного
    # тома с исходниками поверх образа.
    reload = os.environ.get("UVICORN_RELOAD", "true").lower() == "true"

    uvicorn.run("app.api:app", host=host, port=port, reload=reload)
