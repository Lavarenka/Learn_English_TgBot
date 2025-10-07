import telebot
from telebot import types
import random
from key import BOT_TOKEN
import questions

bot = telebot.TeleBot(BOT_TOKEN)

# Уровни сложности
DIFFICULTY_LEVELS = {
    'beginner': {
        'name': '🟢 Начальный',
        'file': 'beginner.txt',
        'description': 'Простые слова и базовые фразы'
    },
    'intermediate': {
        'name': '🟡 Средний',
        'file': 'intermediate.txt',
        'description': 'Повседневная лексика и выражения'
    },
    'advanced': {
        'name': '🔴 Продвинутый',
        'file': 'advanced.txt',
        'description': 'Сложные слова и идиомы'
    },
    'mixed': {
        'name': '🌈 Смешанный',
        'file': None,
        'description': 'Слова из всех уровней сложности'
    }
}

# Словари для хранения данных
user_games = {}
user_stats = {}
user_settings = {}


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
    btn1 = types.KeyboardButton('🔢 Количество вопросов')
    btn2 = types.KeyboardButton('🎯 Уровень сложности')
    btn3 = types.KeyboardButton('📝 Текущие настройки')
    btn4 = types.KeyboardButton('⬅️ Назад')
    markup.add(btn1, btn2, btn3, btn4)
    return markup


# Функция для создания меню выбора сложности
def create_difficulty_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for level_key, level_info in DIFFICULTY_LEVELS.items():
        markup.add(types.KeyboardButton(level_info['name']))
    markup.add(types.KeyboardButton('⬅️ Назад'))
    return markup


# Функция для создания меню выбора количества вопросов
def create_questions_count_menu():
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    counts = [5, 10, 15, 20, 25, 30, 40, 50]
    buttons = [types.KeyboardButton(f'{count}') for count in counts]

    for i in range(0, len(buttons), 4):
        markup.add(*buttons[i:i + 4])

    markup.add(types.KeyboardButton('⬅️ Назад'))
    return markup


# Функция для создания игровой клавиатуры
def create_game_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('💡 Подсказка')
    btn2 = types.KeyboardButton('⏭️ Пропустить')
    btn3 = types.KeyboardButton('❌ Завершить игру')
    markup.add(btn1, btn2, btn3)
    return markup


# Функции для работы с настройками пользователя
def get_user_settings(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {
            'questions_count': 10,
            'difficulty': 'beginner'
        }
    return user_settings[user_id]


def get_user_questions_count(user_id):
    return get_user_settings(user_id)['questions_count']


def get_user_difficulty(user_id):
    return get_user_settings(user_id)['difficulty']


def set_user_questions_count(user_id, count):
    user_settings[user_id]['questions_count'] = count


def set_user_difficulty(user_id, difficulty):
    user_settings[user_id]['difficulty'] = difficulty


# Функция для загрузки вопросов по уровню сложности
def load_questions_by_difficulty(difficulty):
    level_info = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS['beginner'])

    if difficulty == 'mixed':
        # Для смешанного уровня загружаем все файлы
        all_questions = []
        for level_key, level_data in DIFFICULTY_LEVELS.items():
            if level_key != 'mixed' and level_data['file']:
                questions_list = questions.parse_questions_from_file(level_data['file'])
                all_questions.extend(questions_list)
        return all_questions
    else:
        # Для конкретного уровня загружаем соответствующий файл
        if level_info['file']:
            return questions.parse_questions_from_file(level_info['file'])

    # Если файл не найден, используем базовый
    return questions.parse_questions_from_file('base.txt')


# Функция для начала новой игры
def start_new_game(user_id):
    settings = get_user_settings(user_id)
    questions_count = settings['questions_count']
    difficulty = settings['difficulty']

    # Загружаем вопросы для выбранного уровня сложности
    difficulty_questions = load_questions_by_difficulty(difficulty)

    # Проверяем, что есть достаточно вопросов
    available_questions = min(questions_count, len(difficulty_questions))

    if available_questions == 0:
        return None, "❌ Для выбранного уровня сложности нет доступных вопросов"

    user_games[user_id] = {
        'score': 0,
        'current_question': 0,
        'questions': random.sample(difficulty_questions, available_questions),
        'in_game': True,
        'hint_used': False,
        'questions_count': available_questions,
        'difficulty': difficulty
    }

    return send_question(user_id), None


# Функция для отправки вопроса
def send_question(user_id):
    game_data = user_games[user_id]
    question_data = game_data['questions'][game_data['current_question']]

    question_text = f"❓ Вопрос {game_data['current_question'] + 1} из {game_data['questions_count']}:\n\n{question_data['question']}"

    # Показываем возможные варианты, если их несколько
    if len(question_data['correct']) > 1:
        question_text += f"\n\n💭 Возможные варианты: {', '.join(question_data['correct'])}"

    if game_data['hint_used']:
        question_text += f"\n\n💡 Подсказка: {question_data['hint']}"

    return question_text


# Функция для проверки ответа
def check_answer(user_answer, correct_answers):
    user_clean = user_answer.lower().strip()

    for correct in correct_answers:
        correct_clean = correct.lower().strip()
        if user_clean == correct_clean:
            return True
        if correct_clean in user_clean or user_clean in correct_clean:
            return True

    return False


# Функция для форматирования правильных ответов
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
    difficulty = get_user_difficulty(user_id)
    difficulty_name = DIFFICULTY_LEVELS.get(difficulty, {}).get('name', 'Неизвестно')

    stats_text = f"""📊 Ваша статистика:

🎮 Сыграно игр: {stats['games_played']}
✅ Правильных ответов: {stats['total_correct']} из {stats['total_questions']}
🎯 Точность: {accuracy:.1f}%
🏆 Лучший результат: {stats['best_score']}/{questions_count}
🎯 Текущий уровень: {difficulty_name}"""

    return stats_text


# Функция для получения текста настроек
def get_settings_text(user_id):
    settings = get_user_settings(user_id)
    questions_count = settings['questions_count']
    difficulty = settings['difficulty']
    difficulty_info = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS['beginner'])

    # Загружаем вопросы для текущего уровня
    current_questions = load_questions_by_difficulty(difficulty)

    settings_text = f"""⚙️ Текущие настройки:

🔢 Количество вопросов: {questions_count}
🎯 Уровень сложности: {difficulty_info['name']}
📝 Описание: {difficulty_info['description']}
📚 Доступно слов: {len(current_questions)}"""

    return settings_text


# Функция для завершения игры
def finish_game(user_id, message_chat_id):
    if user_id in user_games:
        game_data = user_games[user_id]
        score = game_data['score']
        total = game_data['questions_count']
        difficulty = game_data['difficulty']
        difficulty_name = DIFFICULTY_LEVELS.get(difficulty, {}).get('name', 'Неизвестно')

        # Сохраняем статистику
        if game_data['current_question'] > 0:
            update_stats(user_id, score, total)

        # Результат в зависимости от счета
        if score == total:
            result_text = f"🎊 Поздравляю! На уровне {difficulty_name} все {total} ответов верны! 🌟"
        elif score >= total * 0.7:
            result_text = f"👍 Отличный результат! {score} из {total} на уровне {difficulty_name}"
        elif score >= total * 0.5:
            result_text = f"👌 Хорошо! {score} из {total} на уровне {difficulty_name}"
        else:
            result_text = f"💪 Попробуй еще! {score} из {total} на уровне {difficulty_name}"

        bot.send_message(message_chat_id, result_text, reply_markup=create_main_menu())
        del user_games[user_id]
    else:
        bot.send_message(message_chat_id, "👋 Игра завершена", reply_markup=create_main_menu())


# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    difficulty_info = DIFFICULTY_LEVELS.get(settings['difficulty'], DIFFICULTY_LEVELS['beginner'])
    current_questions = load_questions_by_difficulty(settings['difficulty'])

    welcome_text = f"""🎯 Добро пожаловать в Английскую Викторину!

Текущие настройки:
🎯 Уровень: {difficulty_info['name']}
🔢 Вопросов: {settings['questions_count']}
📚 Доступно слов: {len(current_questions)}

{difficulty_info['description']}

Используй меню ниже для начала игры! 🍀"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu())


@bot.message_handler(commands=['game'])
def start_game_command(message):
    user_id = message.from_user.id
    question_text, error = start_new_game(user_id)

    if error:
        bot.send_message(message.chat.id, error, reply_markup=create_main_menu())
    else:
        settings = get_user_settings(user_id)
        difficulty_info = DIFFICULTY_LEVELS.get(settings['difficulty'], DIFFICULTY_LEVELS['beginner'])

        bot.send_message(message.chat.id,
                         f"🎮 Игра началась! Уровень: {difficulty_info['name']}\nВопросов: {settings['questions_count']}\n\nВводи перевод:",
                         reply_markup=create_game_keyboard())
        bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())


@bot.message_handler(commands=['stats'])
def show_stats_command(message):
    user_id = message.from_user.id
    stats_text = get_stats_text(user_id)
    bot.send_message(message.chat.id, stats_text, reply_markup=create_main_menu())


@bot.message_handler(commands=['settings'])
def show_settings_command(message):
    user_id = message.from_user.id
    settings_text = get_settings_text(user_id)
    bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())


# Основной обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_game(message):
    user_id = message.from_user.id

    if message.text == '🎮 Начать игру':
        question_text, error = start_new_game(user_id)

        if error:
            bot.send_message(message.chat.id, error, reply_markup=create_main_menu())
        else:
            settings = get_user_settings(user_id)
            difficulty_info = DIFFICULTY_LEVELS.get(settings['difficulty'], DIFFICULTY_LEVELS['beginner'])

            bot.send_message(message.chat.id,
                             f"🎮 Игра началась! Уровень: {difficulty_info['name']}\nВопросов: {settings['questions_count']}\n\nВводи перевод:",
                             reply_markup=create_game_keyboard())
            bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())

    elif message.text == '📊 Моя статистика':
        stats_text = get_stats_text(user_id)
        bot.send_message(message.chat.id, stats_text, reply_markup=create_main_menu())

    elif message.text == '⚙️ Настройки':
        settings_text = get_settings_text(user_id)
        bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())

    elif message.text == '🔢 Количество вопросов':
        total_available = len(load_questions_by_difficulty(get_user_difficulty(user_id)))
        max_questions = min(50, total_available)
        text = f"🔢 Выбери количество вопросов (5-{max_questions}):\n\nДоступно слов: {total_available}"
        bot.send_message(message.chat.id, text, reply_markup=create_questions_count_menu())

    elif message.text == '🎯 Уровень сложности':
        text = "🎯 Выбери уровень сложности:\n\n"
        for level_key, level_info in DIFFICULTY_LEVELS.items():
            questions_count = len(load_questions_by_difficulty(level_key))
            text += f"{level_info['name']} - {level_info['description']} ({questions_count} слов)\n"
        bot.send_message(message.chat.id, text, reply_markup=create_difficulty_menu())

    elif message.text == '📝 Текущие настройки':
        settings_text = get_settings_text(user_id)
        bot.send_message(message.chat.id, settings_text, reply_markup=create_settings_menu())

    elif message.text == '⬅️ Назад':
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=create_main_menu())

    # Обработка выбора количества вопросов
    elif message.text.isdigit():
        count = int(message.text)
        total_available = len(load_questions_by_difficulty(get_user_difficulty(user_id)))
        max_questions = min(50, total_available)

        if count < 5:
            bot.send_message(message.chat.id, "❌ Минимум 5 вопросов", reply_markup=create_questions_count_menu())
        elif count > max_questions:
            bot.send_message(message.chat.id,
                             f"❌ Максимум {max_questions} вопросов\nВ базе только {total_available} слов",
                             reply_markup=create_questions_count_menu())
        else:
            set_user_questions_count(user_id, count)
            bot.send_message(message.chat.id, f"✅ Установлено: {count} вопросов", reply_markup=create_settings_menu())

    # Обработка выбора уровня сложности
    elif message.text in [level['name'] for level in DIFFICULTY_LEVELS.values()]:
        for level_key, level_info in DIFFICULTY_LEVELS.items():
            if message.text == level_info['name']:
                set_user_difficulty(user_id, level_key)
                questions_list = load_questions_by_difficulty(level_key)
                bot.send_message(message.chat.id,
                                 f"✅ Установлен уровень: {level_info['name']}\n📚 Доступно слов: {len(questions_list)}",
                                 reply_markup=create_settings_menu())
                break

    elif message.text == '💡 Подсказка':
        if user_id in user_games and user_games[user_id]['in_game']:
            game_data = user_games[user_id]
            if not game_data['hint_used']:
                game_data['hint_used'] = True
                question_data = game_data['questions'][game_data['current_question']]
                hint_text = f"💡 Подсказка: {question_data['hint']}"
                bot.send_message(message.chat.id, hint_text, reply_markup=create_game_keyboard())
            else:
                bot.send_message(message.chat.id, "❌ Подсказка уже использована!", reply_markup=create_game_keyboard())
        else:
            bot.send_message(message.chat.id, "Сначала начни игру!", reply_markup=create_main_menu())

    elif message.text == '⏭️ Пропустить':
        if user_id in user_games and user_games[user_id]['in_game']:
            game_data = user_games[user_id]
            question_data = game_data['questions'][game_data['current_question']]
            correct_text = format_correct_answers(question_data['correct'])

            bot.send_message(message.chat.id, f"⏭️ Пропущено! Правильный ответ: {correct_text}",
                             reply_markup=create_game_keyboard())

            game_data['current_question'] += 1
            game_data['hint_used'] = False

            if game_data['current_question'] < game_data['questions_count']:
                question_text = send_question(user_id)
                bot.send_message(message.chat.id, question_text, reply_markup=create_game_keyboard())
            else:
                finish_game(user_id, message.chat.id)

    elif message.text == '❌ Завершить игру':
        if user_id in user_games and user_games[user_id]['in_game']:
            bot.send_message(message.chat.id, "🛑 Игра завершена", reply_markup=create_main_menu())
            finish_game(user_id, message.chat.id)
        else:
            bot.send_message(message.chat.id, "Нет активной игры", reply_markup=create_main_menu())

    # Обработка ответов пользователя
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
            finish_game(user_id, message.chat.id)

    else:
        bot.send_message(message.chat.id, "Выбери действие из меню:", reply_markup=create_main_menu())


# Запуск бота
if __name__ == '__main__':
    print("✅ Бот запущен с системой уровней сложности!")
    bot.polling(none_stop=True)