🎯 English Quiz Bot - Telegram Vocabulary Trainer
https://img.shields.io/badge/Python-3.7+-blue.svg
https://img.shields.io/badge/Telegram-Bot-blue.svg
https://img.shields.io/badge/License-MIT-green.svg

Умный Telegram бот для изучения английской лексики через интерактивную викторину. Бот помогает запоминать перевод слов с поддержкой множественных вариантов ответов и гибкой системой проверки.

✨ Особенности
🎮 Интерактивная викторина - угадывайте перевод английских слов

🔢 Настраиваемая сложность - от 5 до 50 вопросов в игре

💡 Система подсказок - помощь при затруднениях

📊 Детальная статистика - отслеживание прогресса обучения

🔄 Несколько вариантов ответов - поддержка слов с разными переводами

⏭️ Пропуск вопросов - возможность пропустить сложный вопрос

📚 Гибкая база слов - легко добавлять новые слова через текстовый файл

🚀 Быстрый старт
Предварительные требования
Python 3.7 или выше

Аккаунт в Telegram

Токен бота от BotFather

Установка
Клонируйте репозиторий:

bash
git clone https://github.com/your-username/english-quiz-bot.git
cd english-quiz-bot
Установите зависимости:

bash
pip install pyTelegramBotAPI
Создайте файл с токеном бота:

python
# key.py
BOT_TOKEN = 'your_bot_token_here'
Подготовьте базу слов:

txt
# base.txt
You ты/вы .
he он .
she она .
it оно/это .
we мы .
they они .
to be быть/являться .
good хороший/хорошо/добрый .
book книга/бронировать .
Запустите бота:

bash
python quiz_bot.py
