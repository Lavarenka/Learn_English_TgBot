"""
Одноразовый скрипт миграции старых .txt файлов в базу данных.

Запуск (из корня проекта):
    python scripts/seed_from_txt.py

Берёт файлы из папки txt/ (в том же формате "слово|ответ|подсказка",
как раньше) и создаёт для каждого файла отдельный уровень в БД со всеми
его вопросами. Если уровень с таким key уже существует — файл пропускается,
чтобы не задвоить данные при повторном запуске.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app import crud

# Соответствие: файл -> (key, name, description) — взято из старого main.py,
# из словаря DIFFICULTY_LEVELS.
LEVELS_TO_IMPORT = [
    ("txt/beginner.txt", "beginner", "🟢 Начальный", "Простые слова и базовые фразы"),
    ("txt/rent_a_house.txt", "rent_a_house", "🟢 6.Rent a house", "Тема Rent a house"),
    ("txt/intermediate.txt", "intermediate", "🟡 Средний", "Повседневная лексика и выражения"),
    ("txt/advanced.txt", "advanced", "🔴 Продвинутый", "Сложные слова и идиомы"),
    ("txt/irregular-verbs.txt", "irregular_verbs", "🔴 Неправильные глаголы", "Неправильные глаголы"),
    ("txt/irregular-verbs2.txt", "irregular_verbs2", "🔴 Неправильные глаголы 2", "Неправильные глаголы"),
    ("txt/irregular-verbs3.txt", "irregular_verbs3", "🔴 Неправильные глаголы 3", "Неправильные глаголы"),
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        for rel_path, key, name, description in LEVELS_TO_IMPORT:
            file_path = PROJECT_ROOT / rel_path

            if not file_path.exists():
                print(f"⚠️  Пропущено: файл {rel_path} не найден")
                continue

            existing = crud.get_level_by_key(db, key)
            if existing:
                print(f"⏭️  Уровень '{key}' уже есть в базе, пропускаю файл {rel_path}")
                continue

            text = file_path.read_text(encoding="utf-8")
            level = crud.create_level(db, key=key, name=name, description=description)
            added, skipped = crud.bulk_add_questions_from_text(db, level.id, text)

            print(f"✅ Уровень '{key}' ({name}): импортировано {added} вопросов из {rel_path}")
            for line in skipped:
                print(f"   ⚠️ {line}")

        print("\nГотово. Текущие уровни в базе:")
        for level in crud.get_levels(db):
            count = crud.count_questions(db, level.id)
            print(f"  [{level.id}] {level.key} — {level.name} — {count} вопросов")

    finally:
        db.close()


if __name__ == "__main__":
    main()
