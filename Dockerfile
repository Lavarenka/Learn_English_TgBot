# syntax=docker/dockerfile:1

# Один образ используется и для Admin API, и для телеграм-бота —
# у них общий код (app/), разная команда запуска задаётся в
# docker-compose.yml (command: python run_api.py / python run_bot.py).

FROM python:3.11-slim AS base

# Пакеты, которые нужны для сборки psycopg[binary]/bcrypt на некоторых
# платформах, и curl для healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ставим зависимости отдельным слоем — пересобираются только при
# изменении requirements.txt, а не при каждом изменении кода.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Непривилегированный пользователь — запускать процесс от root внутри
# контейнера в продакшене считается плохой практикой.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Дефолтная команда — Admin API. В docker-compose бот переопределяет её
# на "python run_bot.py".
CMD ["python", "run_api.py"]
