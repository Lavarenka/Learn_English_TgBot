"""
Парсер текста в формате "блокнота":

    слово | ответ1/ответ2 | подсказка

Одна строка — один вопрос. Пустые строки и строки без двух разделителей
'|' пропускаются (с указанием номера строки, чтобы было легче найти ошибку).
"""
from dataclasses import dataclass


@dataclass
class ParsedQuestion:
    question: str
    correct: str
    hint: str


@dataclass
class ParseResult:
    questions: list[ParsedQuestion]
    skipped_lines: list[tuple[int, str]]  # (номер строки, содержимое)


def parse_questions_text(text: str) -> ParseResult:
    questions: list[ParsedQuestion] = []
    skipped: list[tuple[int, str]] = []

    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split("|")
        if len(parts) < 3:
            skipped.append((line_num, raw_line))
            continue

        question = parts[0].strip()
        correct = parts[1].strip()
        hint = "|".join(parts[2:]).strip()

        if not question or not correct:
            skipped.append((line_num, raw_line))
            continue

        questions.append(ParsedQuestion(question=question, correct=correct, hint=hint))

    return ParseResult(questions=questions, skipped_lines=skipped)
