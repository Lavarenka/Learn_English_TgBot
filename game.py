from key import BOT_TOKEN
import telebot
from telebot import types
import random

BOT_TOKEN = BOT_TOKEN
bot = telebot.TeleBot(BOT_TOKEN)

# База вопросов и ответов
quiz_questions = [
    {
        "question": "You",
        "correct": "ты",
        "hint": "."
    },
    {
        "question": "he",
        "correct": "он",
        "hint": "."
    },
    {
        "question": "she",
        "correct": "она",
        "hint": "."
    },
    {
        "question": "it",
        "correct": "оно",
        "hint": "."
    },
    {
        "question": "we",
        "correct": "мы",
        "hint": "."
    },
    {
        "question": "they",
        "correct": "они",
        "hint": "."
    },
    {
        "question": "to be",
        "correct": "быть",
        "hint": "."
    }
]

# Словари для хранения состояния игры и статистики пользователей
user_games = {}
user_stats = {}


# Функция для создания игрового меню
def create_game_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🎮 Начать игру')
    btn2 = types.KeyboardButton('📊 Моя статистика')
    btn3 = types.KeyboardButton('💡 Подсказка')
    btn4 = types.KeyboardButton('❌ Сдаться')
    markup.add(btn1, btn2, btn3, btn4)
    return markup


# Функция для создания клавиатуры во время игры
def create_game_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('💡 Подсказка')
    btn2 = types.KeyboardButton('❌ Сдаться')
    markup.add(btn1, btn2)
    return markup


# Функция для начала новой игры
def start_new_game(user_id):
    user_games[user_id] = {
        'score': 0,
        'current_question': 0,
        'questions': random.sample(quiz_questions, min(5, len(quiz_questions))),  # 5 случайных вопроса
        'in_game': True,
        'hint_used': False
    }
    return send_question(user_id)


# Функция для отправки вопроса
def send_question(user_id):
    game_data = user_games[user_id]
    question_data = game_data['questions'][game_data['current_question']]

    question_text = f"❓ Вопрос {game_data['current_question'] + 1} из {len(game_data['questions'])}:\n\n{question_data['question']}"

    if game_data['hint_used']:
        question_text += f"\n\n💡 Подсказка: {question_data['hint']}"

    return question_text


# Функция для проверки ответа (более гибкая проверка)
def check_answer(user_answer, correct_answer):
    # Приводим оба ответа к нижнему регистру и убираем пробелы
    user_clean = user_answer.lower().strip()
    correct_clean = correct_answer.lower().strip()

    # Проверяем точное совпадение
    if user_clean == correct_clean:
        return True

    # Дополнительные проверки для чисел
    if correct_clean.isdigit() and user_clean.isdigit():
        return user_clean == correct_clean

    # Проверяем частичное совпадение для текстовых ответов
    if correct_clean in user_clean or user_clean in correct_clean:
        return True

    return False


# Функция для обновления статистики
def update_stats(user_id, score, total_questions):
    if user_id not in user_stats:
        user_stats[user_id] = {
            'games_played': 0,
            'total_correct': 0,
            'total_questions': 0,
            'best_score': 0
        }

    stats = user_stats[user_id]
    stats['games_played'] += 1
    stats['total_correct'] += score
    stats['total_questions'] += total_questions

    if score > stats['best_score']:
        stats['best_score'] = score


# Функция для получения статистики
def get_stats_text(user_id):
    if user_id not in user_stats:
        return "📊 Вы еще не играли. Начните игру, чтобы увидеть статистику!"

    stats = user_stats[user_id]

    if stats['games_played'] == 0:
        return "📊 Вы еще не играли. Начните игру, чтобы увидеть статистику!"

    accuracy = (stats['total_correct'] / stats['total_questions']) * 100 if stats['total_questions'] > 0 else 0

    stats_text = f"""📊 Ваша статистика:

🎮 Сыграно игр: {stats['games_played']}
✅ Правильных ответов: {stats['total_correct']} из {stats['total_questions']}
🎯 Точность: {accuracy:.1f}%
🏆 Лучший результат: {stats['best_score']}/5 правильных ответов"""

    return stats_text


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """🎯 Добро пожаловать в Викторину!

Я задам тебе 5 вопросов. Тебе нужно будет вписать ответ самостоятельно, а не выбирать из вариантов.

💡 Можно использовать подсказку для текущего вопроса
❌ Можно сдаться и перейти к следующему вопросу

Удачи! 🍀"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_game_menu())


# Обработчик команды /game
@bot.message_handler(commands=['game'])
def start_game_command(message):
    user_id = message.from_user.id
    start_new_game(user_id)
    question_text = send_question(user_id)
    bot.send_message(message.chat.id, "🎮 Игра началась! Вводи ответ текстом:", reply_markup=create_game_keyboard())
    bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())


# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def show_stats_command(message):
    user_id = message.from_user.id
    stats_text = get_stats_text(user_id)
    bot.send_message(message.chat.id, stats_text, reply_markup=create_game_menu())


# Обработка нажатий кнопок меню
@bot.message_handler(func=lambda message: True)
def handle_game(message):
    user_id = message.from_user.id

    if message.text == '🎮 Начать игру':
        start_new_game(user_id)
        question_text = send_question(user_id)
        bot.send_message(message.chat.id, "🎮 Игра началась! Вводи ответ текстом:", reply_markup=create_game_keyboard())
        bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())

    elif message.text == '📊 Моя статистика':
        stats_text = get_stats_text(user_id)
        bot.send_message(message.chat.id, stats_text, reply_markup=create_game_menu())

    elif message.text == '💡 Подсказка':
        if user_id in user_games and user_games[user_id]['in_game']:
            game_data = user_games[user_id]
            if not game_data['hint_used']:
                game_data['hint_used'] = True
                question_data = game_data['questions'][game_data['current_question']]
                hint_text = f"💡 Подсказка: {question_data['hint']}"
                bot.send_message(message.chat.id, hint_text, reply_markup=create_game_keyboard())
            else:
                bot.send_message(message.chat.id, "❌ Подсказка уже использована для этого вопроса!",
                                 reply_markup=create_game_keyboard())
        else:
            bot.send_message(message.chat.id, "Сначала начни игру!", reply_markup=create_game_menu())

    elif message.text == '❌ Сдаться':
        if user_id in user_games and user_games[user_id]['in_game']:
            game_data = user_games[user_id]
            correct_answer = game_data['questions'][game_data['current_question']]['correct']

            bot.send_message(message.chat.id, f"😔 Правильный ответ был: {correct_answer}",
                             reply_markup=create_game_keyboard())

            # Переход к следующему вопросу
            game_data['current_question'] += 1
            game_data['hint_used'] = False

            if game_data['current_question'] < len(game_data['questions']):
                question_text = send_question(user_id)
                bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())
            else:
                # Игра завершена
                score = game_data['score']
                total = len(game_data['questions'])
                update_stats(user_id, score, total)

                result_text = f"🎮 Игра завершена!\n✅ Правильных ответов: {score} из {total}"
                bot.send_message(message.chat.id, result_text, reply_markup=create_game_menu())
                del user_games[user_id]
        else:
            bot.send_message(message.chat.id, "👋 Игра завершена. Чтобы начать заново, нажми 'Начать игру'",
                             reply_markup=create_game_menu())

    # Обработка текстовых ответов (если пользователь в игре)
    elif user_id in user_games and user_games[user_id]['in_game']:
        game_data = user_games[user_id]
        current_question = game_data['questions'][game_data['current_question']]

        if check_answer(message.text, current_question['correct']):
            game_data['score'] += 1
            bot.send_message(message.chat.id, "✅ Правильно! 🎉", reply_markup=create_game_keyboard())
        else:
            bot.send_message(message.chat.id, f"❌ Неправильно! Правильный ответ: {current_question['correct']}",
                             reply_markup=create_game_keyboard())

        # Переход к следующему вопросу
        game_data['current_question'] += 1
        game_data['hint_used'] = False

        if game_data['current_question'] < len(game_data['questions']):
            question_text = send_question(user_id)
            bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())
        else:
            # Игра завершена
            score = game_data['score']
            total = len(game_data['questions'])
            update_stats(user_id, score, total)

            if score == total:
                result_text = f"🎊 Поздравляю! Ты ответил правильно на все {total} вопросов! Ты гений! 🌟"
            elif score >= total / 2:
                result_text = f"👍 Хороший результат! {score} из {total} правильных ответов!"
            else:
                result_text = f"😊 Неплохо! {score} из {total}. Попробуй еще раз!"

            bot.send_message(message.chat.id, result_text, reply_markup=create_game_menu())
            del user_games[user_id]

    else:
        # Если пользователь не в игре
        bot.send_message(message.chat.id, "Выбери действие из меню ниже:", reply_markup=create_game_menu())


# Запускаем бота
if __name__ == '__main__':
    print("Игровой бот запущен...")
    bot.polling(none_stop=True)