import telebot
from telebot import types
import random
from key import BOT_TOKEN
import questions

quiz_questions = questions.parse_questions_from_file('base.txt')

bot = telebot.TeleBot(BOT_TOKEN)

# Словари для хранения состояния игры и статистики пользователей
user_games = {}
user_stats = {}
user_settings = {}  # Для хранения настроек пользователя


# Функция для создания главного меню
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🎮 Начать игру')
    btn2 = types.KeyboardButton('📊 Моя статистика')
    btn3 = types.KeyboardButton('⚙️ Настройки')
    markup.add(btn1, btn2, btn3)
    return markup


# Функция для создания меню настроек
def create_settings_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🔢 Изменить количество вопросов')
    btn2 = types.KeyboardButton('📝 Текущие настройки')
    btn3 = types.KeyboardButton('⬅️ Назад')
    markup.add(btn1, btn2, btn3)
    return markup


# Функция для создания клавиатуры выбора количества вопросов
def create_questions_count_menu():
    markup = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)
    buttons = []
    # Создаем кнопки для выбора количества вопросов
    counts = [5, 10, 15, 20, 25, 30, 40, 50]
    for count in counts:
        buttons.append(types.KeyboardButton(f'{count} вопросов'))

    # Разбиваем на строки по 4 кнопки
    for i in range(0, len(buttons), 4):
        markup.add(*buttons[i:i + 4])

    markup.add(types.KeyboardButton('⬅️ Назад'))
    return markup


# Функция для создания клавиатуры во время игры
def create_game_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('💡 Подсказка')
    btn2 = types.KeyboardButton('⏭️ Пропустить')
    btn3 = types.KeyboardButton('❌ Завершить игру')
    markup.add(btn1, btn2, btn3)
    return markup


# Функция для получения количества вопросов по умолчанию для пользователя
def get_user_questions_count(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {'questions_count': 10}  # По умолчанию 10 вопросов
    return user_settings[user_id]['questions_count']


# Функция для установки количества вопросов
def set_user_questions_count(user_id, count):
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]['questions_count'] = count


# Функция для начала новой игры
def start_new_game(user_id):
    questions_count = get_user_questions_count(user_id)
    available_questions = min(questions_count, len(quiz_questions))

    user_games[user_id] = {
        'score': 0,
        'current_question': 0,
        'questions': random.sample(quiz_questions, available_questions),
        'in_game': True,
        'hint_used': False,
        'questions_count': available_questions
    }
    return send_question(user_id)


# Функция для отправки вопроса
def send_question(user_id):
    game_data = user_games[user_id]
    question_data = game_data['questions'][game_data['current_question']]

    question_text = f"❓ Вопрос {game_data['current_question'] + 1} из {game_data['questions_count']}:\n\n{question_data['question']}"

    # Показываем возможные варианты, если их несколько
    # if len(question_data['correct']) > 1:
    #     question_text += f"\n\n💭 Возможные варианты: {', '.join(question_data['correct'])}"

    if game_data['hint_used']:
        question_text += f"\n\n💡 Подсказка: {question_data['hint']}"

    return question_text


# Обновленная функция для проверки ответа с поддержкой множественных вариантов
def check_answer(user_answer, correct_answers):
    """
    Проверяет ответ пользователя против списка правильных вариантов
    """
    user_clean = user_answer.lower().strip()

    for correct in correct_answers:
        correct_clean = correct.lower().strip()

        # Точное совпадение
        if user_clean == correct_clean:
            return True

        # Частичное совпадение для текстовых ответов
        if correct_clean in user_clean or user_clean in correct_clean:
            return True

    return False


# Функция для форматирования правильных ответов в красивый текст
def format_correct_answers(correct_answers):
    if len(correct_answers) == 1:
        return correct_answers[0]
    else:
        return " или ".join(correct_answers)


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
    questions_count = get_user_questions_count(user_id)

    stats_text = f"""📊 Ваша статистика:

🎮 Сыграно игр: {stats['games_played']}
✅ Правильных ответов: {stats['total_correct']} из {stats['total_questions']}
🎯 Точность: {accuracy:.1f}%
🏆 Лучший результат: {stats['best_score']}/{questions_count} правильных ответов
🔢 Текущее количество вопросов: {questions_count}"""

    return stats_text


# Функция для получения текста текущих настроек
def get_settings_text(user_id):
    questions_count = get_user_questions_count(user_id)
    total_available = len(quiz_questions)

    settings_text = f"""⚙️ Текущие настройки:

🔢 Количество вопросов в игре: {questions_count}
📚 Доступно слов в базе: {total_available}

💡 Максимальное количество вопросов: {min(50, total_available)}"""

    return settings_text


# Функция для завершения игры
def finish_game(user_id, message_chat_id):
    if user_id in user_games:
        game_data = user_games[user_id]
        score = game_data['score']
        total = game_data['questions_count']

        # Сохраняем статистику только если игра была начата
        if game_data['current_question'] > 0:
            update_stats(user_id, score, total)

        if score == total:
            result_text = f"🎊 Поздравляю! Ты ответил правильно на все {total} вопросов! Ты гений! 🌟"
        elif score >= total * 0.8:
            result_text = f"👍 Отличный результат! {score} из {total} правильных ответов!"
        elif score >= total * 0.6:
            result_text = f"👌 Хороший результат! {score} из {total} правильных ответов!"
        elif score >= total * 0.4:
            result_text = f"😊 Неплохо! {score} из {total} правильных ответов!"
        else:
            result_text = f"📚 Есть куда расти! {score} из {total} правильных ответов. Попробуй еще раз!"

        bot.send_message(message_chat_id, result_text, reply_markup=create_main_menu())
        del user_games[user_id]
    else:
        bot.send_message(message_chat_id, "👋 Игра завершена. Чтобы начать заново, нажми 'Начать игру'",
                         reply_markup=create_main_menu())


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    total_questions = len(quiz_questions)
    user_questions_count = get_user_questions_count(message.from_user.id)

    welcome_text = f"""🎯 Добро пожаловать в Викторину по английскому!

В базе: {total_questions} слов
Текущее количество вопросов в игре: {user_questions_count}

💡 Некоторые слова имеют несколько правильных переводов
💡 Можно использовать подсказку для текущего вопроса
⏭️ Можно пропустить вопрос
❌ Можно завершить игру досрочно

Используй меню ниже для управления игрой! 🍀"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu())


# Обработчик команды /game
@bot.message_handler(commands=['game'])
def start_game_command(message):
    user_id = message.from_user.id
    start_new_game(user_id)
    question_text = send_question(user_id)
    questions_count = get_user_questions_count(user_id)

    bot.send_message(message.chat.id,
                     f"🎮 Игра началась! Всего вопросов: {questions_count}\nВводи перевод текстом:",
                     reply_markup=create_game_keyboard())
    bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())


# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def show_stats_command(message):
    user_id = message.from_user.id
    stats_text = get_stats_text(user_id)
    bot.send_message(message.chat.id, stats_text, reply_markup=create_main_menu())


# Обработчик команды /settings
@bot.message_handler(commands=['settings'])
def show_settings_command(message):
    user_id = message.from_user.id
    settings_text = get_settings_text(user_id)
    bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())


# Обработка нажатий кнопок меню
@bot.message_handler(func=lambda message: True)
def handle_game(message):
    user_id = message.from_user.id

    if message.text == '🎮 Начать игру':
        start_new_game(user_id)
        question_text = send_question(user_id)
        questions_count = get_user_questions_count(user_id)

        bot.send_message(message.chat.id,
                         f"🎮 Игра началась! Всего вопросов: {questions_count}\nВводи перевод текстом:",
                         reply_markup=create_game_keyboard())
        bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())

    elif message.text == '📊 Моя статистика':
        stats_text = get_stats_text(user_id)
        bot.send_message(message.chat.id, stats_text, reply_markup=create_main_menu())

    elif message.text == '⚙️ Настройки':
        settings_text = get_settings_text(user_id)
        bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())

    elif message.text == '🔢 Изменить количество вопросов':
        total_available = len(quiz_questions)
        max_questions = min(50, total_available)
        text = f"🔢 Выбери количество вопросов для игры:\n\nДоступно слов в базе: {total_available}\nМаксимум: {max_questions} вопросов"
        bot.send_message(message.chat.id, text, reply_markup=create_questions_count_menu())

    elif message.text == '📝 Текущие настройки':
        settings_text = get_settings_text(user_id)
        bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())

    elif message.text == '⬅️ Назад':
        bot.send_message(message.chat.id, "Возвращаемся в главное меню:", reply_markup=create_main_menu())

    elif message.text.endswith('вопросов') and message.text.split()[0].isdigit():
        # Обработка выбора количества вопросов
        try:
            count = int(message.text.split()[0])
            total_available = len(quiz_questions)
            max_questions = min(50, total_available)

            if count < 5:
                bot.send_message(message.chat.id, "❌ Минимальное количество вопросов: 5",
                                 reply_markup=create_questions_count_menu())
            elif count > max_questions:
                bot.send_message(message.chat.id,
                                 f"❌ Максимальное количество вопросов: {max_questions}\nВ базе только {total_available} слов",
                                 reply_markup=create_questions_count_menu())
            else:
                set_user_questions_count(user_id, count)
                bot.send_message(message.chat.id, f"✅ Установлено количество вопросов: {count}",
                                 reply_markup=create_settings_menu())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Ошибка при выборе количества вопросов",
                             reply_markup=create_settings_menu())

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
            bot.send_message(message.chat.id, "Сначала начни игру!", reply_markup=create_main_menu())

    elif message.text == '⏭️ Пропустить':
        if user_id in user_games and user_games[user_id]['in_game']:
            game_data = user_games[user_id]
            question_data = game_data['questions'][game_data['current_question']]
            correct_text = format_correct_answers(question_data['correct'])

            bot.send_message(message.chat.id, f"⏭️ Пропущено! Правильный ответ: {correct_text}",
                             reply_markup=create_game_keyboard())

            # Переход к следующему вопросу
            game_data['current_question'] += 1
            game_data['hint_used'] = False

            if game_data['current_question'] < game_data['questions_count']:
                question_text = send_question(user_id)
                bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())
            else:
                # Игра завершена естественным путем
                finish_game(user_id, message.chat.id)

    elif message.text == '❌ Завершить игру':
        if user_id in user_games and user_games[user_id]['in_game']:
            bot.send_message(message.chat.id, "🛑 Игра завершена досрочно",
                             reply_markup=create_main_menu())
            finish_game(user_id, message.chat.id)
        else:
            bot.send_message(message.chat.id, "👋 Нет активной игры. Чтобы начать, нажми 'Начать игру'",
                             reply_markup=create_main_menu())

    elif user_id in user_games and user_games[user_id]['in_game']:
        game_data = user_games[user_id]
        current_question = game_data['questions'][game_data['current_question']]

        if check_answer(message.text, current_question['correct']):
            game_data['score'] += 1
            bot.send_message(message.chat.id, "✅ Правильно! 🎉", reply_markup=create_game_keyboard())
        else:
            correct_text = format_correct_answers(current_question['correct'])
            bot.send_message(message.chat.id, f"❌ Неправильно! Правильный ответ: {correct_text}",
                             reply_markup=create_game_keyboard())

        game_data['current_question'] += 1
        game_data['hint_used'] = False

        if game_data['current_question'] < game_data['questions_count']:
            question_text = send_question(user_id)
            bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())
        else:
            # Игра завершена естественным путем
            finish_game(user_id, message.chat.id)

    else:
        bot.send_message(message.chat.id, "Выбери действие из меню ниже:", reply_markup=create_main_menu())


# Запускаем бота
if __name__ == '__main__':
    print(f"✅ Бот запущен! Доступно вопросов: {len(quiz_questions)}")
    bot.polling(none_stop=True)