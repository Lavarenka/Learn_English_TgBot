

def parse_questions_from_file(filename):
    """
    Парсит вопросы из текстового файла
    Формат файла:
    You ты .
    he он .
    she она .
    """
    quiz_questions = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()

                # Пропускаем пустые строки
                if not line:
                    continue

                # Разделяем строку на части
                parts = line.split()

                # Проверяем, что в строке минимум 3 части: вопрос, ответ и подсказка
                if len(parts) < 3:
                    print(f"⚠️ Предупреждение: строка {line_num} пропущена (недостаточно данных): {line}")
                    continue

                # Первое слово - вопрос (английское слово)
                question = parts[0]

                # Разделяем варианты ответов по разделителю "/"
                correct_answers = parts[1].split('/')

                # Все остальное - подсказка (объединяем обратно)
                hint = ' '.join(parts[2:])

                # Создаем словарь вопроса
                question_dict = {
                    "question": question,
                    "correct": correct_answers,
                    "hint": hint
                }

                quiz_questions.append(question_dict)

        print(f"✅ Успешно загружено {len(quiz_questions)} вопросов из файла {filename}")
        return quiz_questions

    except FileNotFoundError:
        print(f"❌ Ошибка: файл {filename} не найден")
        return []
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return []
