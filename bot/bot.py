"""
Telegram-бот "Английская викторина".

В отличие от старой версии, уровни и вопросы теперь читаются не из .txt
файлов, а из базы данных (SQLite + SQLAlchemy). Добавлять новые уровни и
вопросы нужно через Admin API (см. app/api.py и README.md) — файлы .txt
руками редактировать больше не нужно.

Запуск (из корня проекта):
    python run_bot.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import telebot
from telebot import types

from key import BOT_TOKEN
from app.database import SessionLocal, Base, engine
from app import crud

Base.metadata.create_all(bind=engine)

bot = telebot.TeleBot(BOT_TOKEN)

MIXED_KEY = "mixed"  # виртуальный уровень: вопросы из всех уровней сразу

# Данные пользователей — как и раньше, хранятся в памяти процесса
# (сбрасываются при перезапуске бота). При желании потом можно вынести
# в БД отдельными таблицами.
user_games: dict[int, dict] = {}
user_stats: dict[int, dict] = {}
user_settings: dict[int, dict] = {}


# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🎮 Начать игру"),
        types.KeyboardButton("📊 Моя статистика"),
        types.KeyboardButton("⚙️ Настройки"),
    )
    return markup


def create_settings_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔢 Количество вопросов"),
        types.KeyboardButton("🎯 Уровень сложности"),
        types.KeyboardButton("📝 Текущие настройки"),
        types.KeyboardButton("⬅️ Назад"),
    )
    return markup


def create_difficulty_menu(db):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for level in crud.get_levels(db):
        markup.add(types.KeyboardButton(level.name))
    markup.add(types.KeyboardButton("🌈 Смешанный (все уровни)"))
    markup.add(types.KeyboardButton("⬅️ Назад"))
    return markup


def create_questions_count_menu():
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    counts = [5, 10, 15, 20, 25, 30, 40, 50]
    buttons = [types.KeyboardButton(f"{c}") for c in counts]
    for i in range(0, len(buttons), 4):
        markup.add(*buttons[i:i + 4])
    markup.add(types.KeyboardButton("⬅️ Назад"))
    return markup


def create_game_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("💡 Подсказка"),
        types.KeyboardButton("⏭️ Пропустить"),
        types.KeyboardButton("❌ Завершить игру"),
    )
    return markup


# ---------------------------------------------------------------------------
# Настройки пользователя
# ---------------------------------------------------------------------------

def get_user_settings(db, user_id: int) -> dict:
    if user_id not in user_settings:
        first_level = crud.get_levels(db)
        default_key = first_level[0].key if first_level else MIXED_KEY
        user_settings[user_id] = {"questions_count": 10, "difficulty": default_key}
    return user_settings[user_id]


def set_user_questions_count(user_id: int, count: int):
    user_settings[user_id]["questions_count"] = count


def set_user_difficulty(user_id: int, difficulty_key: str):
    user_settings[user_id]["difficulty"] = difficulty_key


def level_display_name(db, level_key: str) -> str:
    if level_key == MIXED_KEY:
        return "🌈 Смешанный (все уровни)"
    level = crud.get_level_by_key(db, level_key)
    return level.name if level else "Неизвестно"


def available_questions_count(db, level_key: str) -> int:
    if level_key == MIXED_KEY:
        return sum(crud.count_questions(db, lv.id) for lv in crud.get_levels(db))
    level = crud.get_level_by_key(db, level_key)
    return crud.count_questions(db, level.id) if level else 0


# ---------------------------------------------------------------------------
# Игровая логика
# ---------------------------------------------------------------------------

def start_new_game(db, user_id: int):
    settings = get_user_settings(db, user_id)
    questions_count = settings["questions_count"]
    difficulty_key = settings["difficulty"]

    if difficulty_key == MIXED_KEY:
        selected = crud.get_random_questions_mixed(db, questions_count)
    else:
        level = crud.get_level_by_key(db, difficulty_key)
        if not level:
            return None, "❌ Уровень не найден. Выберите уровень заново в настройках."
        selected = crud.get_random_questions(db, level.id, questions_count)

    if not selected:
        return None, "❌ Для выбранного уровня сложности нет доступных вопросов"

    if len(selected) < questions_count:
        total = available_questions_count(db, difficulty_key)
        return None, f"❌ В базе только {total} слов. Уменьшите количество вопросов."

    user_games[user_id] = {
        "score": 0,
        "current_question": 0,
        "questions_count": questions_count,
        "questions": selected,  # список объектов Question (detached, но данные уже загружены)
        "in_game": True,
        "hint_used": False,
        "difficulty": difficulty_key,
    }

    return send_question(user_id), None


def send_question(user_id: int) -> str:
    game = user_games[user_id]
    q = game["questions"][game["current_question"]]

    text = f"❓ Вопрос {game['current_question'] + 1} из {game['questions_count']}:\n\n{q.question}"
    if game["hint_used"]:
        text += f"\n\n💡 Подсказка: {q.hint}"
    return text


def check_answer(user_answer: str, correct_answers: list[str]) -> bool:
    user_clean = re.sub(r"\s+", " ", user_answer.lower().strip())
    for correct in correct_answers:
        correct_clean = re.sub(r"\s+", " ", correct.lower().strip())
        if user_clean == correct_clean:
            return True
    return False


def format_correct_answers(correct_answers: list[str]) -> str:
    return correct_answers[0] if len(correct_answers) == 1 else " или ".join(correct_answers)


def update_stats(user_id: int, score: int, total: int):
    if user_id not in user_stats:
        user_stats[user_id] = {"games_played": 0, "total_correct": 0, "total_questions": 0, "best_score": 0}
    stats = user_stats[user_id]
    stats["games_played"] += 1
    stats["total_correct"] += score
    stats["total_questions"] += total
    if score > stats["best_score"]:
        stats["best_score"] = score


def get_stats_text(user_id: int) -> str:
    if user_id not in user_stats or user_stats[user_id]["games_played"] == 0:
        return "📊 Вы еще не играли. Начните игру, чтобы увидеть статистику!"

    stats = user_stats[user_id]
    accuracy = (stats["total_correct"] / stats["total_questions"]) * 100 if stats["total_questions"] else 0

    return f"""📊 Ваша статистика:

🎮 Сыграно игр: {stats['games_played']}
✅ Правильных ответов: {stats['total_correct']} из {stats['total_questions']}
🎯 Точность: {accuracy:.1f}%
🏆 Лучший результат: {stats['best_score']}"""


def get_settings_text(db, user_id: int) -> str:
    settings = get_user_settings(db, user_id)
    difficulty_key = settings["difficulty"]
    name = level_display_name(db, difficulty_key)
    available = available_questions_count(db, difficulty_key)

    return f"""⚙️ Текущие настройки:

🔢 Количество вопросов: {settings['questions_count']}
🎯 Уровень сложности: {name}
📚 Доступно слов: {available}

💡 Вопросы выбираются случайно без повторений"""


def finish_game(db, user_id: int, chat_id: int):
    if user_id in user_games:
        game = user_games[user_id]
        score = game["score"]
        total = game["questions_count"]
        name = level_display_name(db, game["difficulty"])

        if game["current_question"] > 0:
            update_stats(user_id, score, total)

        if score == total:
            result = f"🎊 Поздравляю! На уровне {name} все {total} ответов верны! 🌟"
        elif score >= total * 0.7:
            result = f"👍 Отличный результат! {score} из {total} на уровне {name}"
        elif score >= total * 0.5:
            result = f"👌 Хорошо! {score} из {total} на уровне {name}"
        else:
            result = f"💪 Попробуй еще! {score} из {total} на уровне {name}"

        bot.send_message(chat_id, result, reply_markup=create_main_menu())
        del user_games[user_id]
    else:
        bot.send_message(chat_id, "👋 Игра завершена", reply_markup=create_main_menu())


# ---------------------------------------------------------------------------
# Хендлеры
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    db = SessionLocal()
    try:
        user_id = message.from_user.id
        settings = get_user_settings(db, user_id)
        name = level_display_name(db, settings["difficulty"])
        available = available_questions_count(db, settings["difficulty"])

        text = f"""🎯 Добро пожаловать в Английскую Викторину!

Текущие настройки:
🎯 Уровень: {name}
🔢 Вопросов: {settings['questions_count']}
📚 Доступно слов: {available}

💡 Вопросы выбираются случайно без повторений!

Используй меню ниже для начала игры! 🍀"""
        bot.send_message(message.chat.id, text, reply_markup=create_main_menu())
    finally:
        db.close()


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    db = SessionLocal()
    try:
        _handle_message(db, message)
    finally:
        db.close()


def _handle_message(db, message):
    user_id = message.from_user.id
    text = message.text or ""

    if text == "🎮 Начать игру":
        question_text, error = start_new_game(db, user_id)
        if error:
            bot.send_message(message.chat.id, error, reply_markup=create_main_menu())
            return
        settings = get_user_settings(db, user_id)
        name = level_display_name(db, settings["difficulty"])
        bot.send_message(
            message.chat.id,
            f"🎮 Игра началась! Уровень: {name}\nВопросов: {settings['questions_count']}\n\nВводи перевод:",
            reply_markup=create_game_keyboard(),
        )
        bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())

    elif text == "📊 Моя статистика":
        bot.send_message(message.chat.id, get_stats_text(user_id), reply_markup=create_main_menu())

    elif text == "⚙️ Настройки":
        bot.send_message(message.chat.id, get_settings_text(db, user_id), reply_markup=create_settings_menu())

    elif text == "🔢 Количество вопросов":
        settings = get_user_settings(db, user_id)
        total = available_questions_count(db, settings["difficulty"])
        max_q = min(50, total)
        bot.send_message(
            message.chat.id,
            f"🔢 Выбери количество вопросов (5-{max_q}):\n\nДоступно слов: {total}",
            reply_markup=create_questions_count_menu(),
        )

    elif text == "🎯 Уровень сложности":
        lines = ["🎯 Выбери уровень сложности:\n"]
        for level in crud.get_levels(db):
            count = crud.count_questions(db, level.id)
            lines.append(f"{level.name} - {level.description or ''} ({count} слов)")
        bot.send_message(message.chat.id, "\n".join(lines), reply_markup=create_difficulty_menu(db))

    elif text == "📝 Текущие настройки":
        bot.send_message(message.chat.id, get_settings_text(db, user_id), reply_markup=create_settings_menu())

    elif text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=create_main_menu())

    elif text.isdigit():
        count = int(text)
        settings = get_user_settings(db, user_id)
        total = available_questions_count(db, settings["difficulty"])

        if count < 5:
            bot.send_message(message.chat.id, "❌ Минимум 5 вопросов", reply_markup=create_questions_count_menu())
        elif count > total:
            bot.send_message(
                message.chat.id,
                f"❌ В базе только {total} слов\nМаксимум можно выбрать {total} вопросов",
                reply_markup=create_questions_count_menu(),
            )
        else:
            set_user_questions_count(user_id, count)
            bot.send_message(message.chat.id, f"✅ Установлено: {count} вопросов", reply_markup=create_settings_menu())

    elif text == "🌈 Смешанный (все уровни)":
        set_user_difficulty(user_id, MIXED_KEY)
        total = available_questions_count(db, MIXED_KEY)
        bot.send_message(
            message.chat.id,
            f"✅ Установлен режим: 🌈 Смешанный\n📚 Доступно слов: {total}",
            reply_markup=create_settings_menu(),
        )

    elif any(text == lv.name for lv in crud.get_levels(db)):
        level = next(lv for lv in crud.get_levels(db) if lv.name == text)
        set_user_difficulty(user_id, level.key)
        count = crud.count_questions(db, level.id)
        bot.send_message(
            message.chat.id,
            f"✅ Установлен уровень: {level.name}\n📚 Доступно слов: {count}",
            reply_markup=create_settings_menu(),
        )

    elif text == "💡 Подсказка":
        game = user_games.get(user_id)
        if game and game["in_game"]:
            if not game["hint_used"]:
                game["hint_used"] = True
                q = game["questions"][game["current_question"]]
                bot.send_message(message.chat.id, f"💡 Подсказка: {q.hint}", reply_markup=create_game_keyboard())
            else:
                bot.send_message(message.chat.id, "❌ Подсказка уже использована!", reply_markup=create_game_keyboard())
        else:
            bot.send_message(message.chat.id, "Сначала начни игру!", reply_markup=create_main_menu())

    elif text == "⏭️ Пропустить":
        game = user_games.get(user_id)
        if game and game["in_game"]:
            q = game["questions"][game["current_question"]]
            correct_text = format_correct_answers(q.correct_answers())
            bot.send_message(
                message.chat.id, f"⏭️ Пропущено! Правильный ответ: {correct_text}", reply_markup=create_game_keyboard()
            )
            game["current_question"] += 1
            game["hint_used"] = False
            if game["current_question"] < game["questions_count"]:
                bot.send_message(message.chat.id, send_question(user_id), reply_markup=create_game_keyboard())
            else:
                finish_game(db, user_id, message.chat.id)
        else:
            bot.send_message(message.chat.id, "Нет активной игры", reply_markup=create_main_menu())

    elif text == "❌ Завершить игру":
        game = user_games.get(user_id)
        if game and game["in_game"]:
            bot.send_message(message.chat.id, "🛑 Игра завершена", reply_markup=create_main_menu())
            finish_game(db, user_id, message.chat.id)
        else:
            bot.send_message(message.chat.id, "Нет активной игры", reply_markup=create_main_menu())

    elif user_id in user_games and user_games[user_id]["in_game"]:
        game = user_games[user_id]
        q = game["questions"][game["current_question"]]
        correct_answers = q.correct_answers()
        correct_text = format_correct_answers(correct_answers)

        if check_answer(text, correct_answers):
            game["score"] += 1
            bot.send_message(message.chat.id, f"✅ Правильно! {correct_text} 🎉", reply_markup=create_game_keyboard())
        else:
            bot.send_message(
                message.chat.id, f"❌ Неправильно! Правильный ответ: {correct_text}", reply_markup=create_game_keyboard()
            )

        game["current_question"] += 1
        game["hint_used"] = False

        if game["current_question"] < game["questions_count"]:
            bot.send_message(message.chat.id, send_question(user_id), reply_markup=create_game_keyboard())
        else:
            finish_game(db, user_id, message.chat.id)

    else:
        bot.send_message(message.chat.id, "Выбери действие из меню:", reply_markup=create_main_menu())


def main():
    print("✅ Бот запущен, вопросы читаются из базы данных")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
