# utils/formatter.py - форматирование текста для Telegram
import re


def format_code(text: str) -> str:
    """
    Форматирование блоков кода для Telegram Markdown
    
    Преобразует ```язык код``` в правильный формат для Telegram
    """
    # Замена блоков кода на Telegram формат
    pattern = r'```(\w+)?\n(.*?)```'
    
    def replace_code_block(match):
        language = match.group(1) or ''
        code = match.group(2)
        return f'```{language}\n{code}```'
    
    formatted = re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
    
    return formatted


def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов Markdown
    
    Используется для безопасного вывода текста
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_bold(text: str) -> str:
    """Форматирование жирного текста"""
    return f"*{text}*"


def format_italic(text: str) -> str:
    """Форматирование курсива"""
    return f"_{text}_"


def format_inline_code(text: str) -> str:
    """Форматирование inline кода"""
    return f"`{text}`"


def clean_response(text: str) -> str:
    """
    Очистка ответа от лишних элементов
    
    - Удаляет множественные пустые строки
    - Удаляет пробелы в конце строк
    """
    # Удаление пробелов в конце строк
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
    # Замена множественных пустых строк на одну
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()