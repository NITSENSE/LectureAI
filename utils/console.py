import sys
from typing import Optional


# ANSI цвета
class Colors:
    """ANSI escape codes для цветов в терминале."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Основные цвета
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Яркие цвета
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


def supports_color() -> bool:
    """Проверка поддержки цветов в терминале."""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    """
    Окрашивание текста в указанный цвет.
    
    Args:
        text: Текст для окрашивания
        color: ANSI код цвета
        
    Returns:
        Окрашенный текст
    """
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_header(text: str, width: int = 60) -> None:
    """
    Печать заголовка с рамкой.
    
    Args:
        text: Текст заголовка
        width: Ширина рамки
    """
    print("\n" + "=" * width)
    print(colorize(f"  {text}", Colors.BOLD + Colors.BRIGHT_CYAN))
    print("=" * width)


def print_section(text: str) -> None:
    """
    Печать заголовка секции.
    
    Args:
        text: Текст заголовка
    """
    print(f"\n{colorize('---', Colors.DIM)} {colorize(text, Colors.BOLD)} {colorize('---', Colors.DIM)}")


def print_success(text: str) -> None:
    """
    Печать сообщения об успехе.
    
    Args:
        text: Текст сообщения
    """
    print(colorize(f"[✓] {text}", Colors.BRIGHT_GREEN))


def print_error(text: str) -> None:
    """
    Печать сообщения об ошибке.
    
    Args:
        text: Текст сообщения
    """
    print(colorize(f"[✗] {text}", Colors.BRIGHT_RED))


def print_warning(text: str) -> None:
    """
    Печать предупреждения.
    
    Args:
        text: Текст предупреждения
    """
    print(colorize(f"[!] {text}", Colors.BRIGHT_YELLOW))


def print_info(text: str) -> None:
    """
    Печать информационного сообщения.
    
    Args:
        text: Текст сообщения
    """
    print(colorize(f"[*] {text}", Colors.BRIGHT_BLUE))


def print_menu_item(number: int, text: str) -> None:
    """
    Печать пункта меню.
    
    Args:
        number: Номер пункта
        text: Текст пункта
    """
    num_str = colorize(f"{number}.", Colors.BRIGHT_CYAN)
    print(f"  {num_str} {text}")


def print_separator(char: str = "-", width: int = 40) -> None:
    """
    Печать разделителя.
    
    Args:
        char: Символ разделителя
        width: Ширина разделителя
    """
    print(char * width)


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Получение ввода от пользователя с опциональным значением по умолчанию.
    
    Args:
        prompt: Текст приглашения
        default: Значение по умолчанию
        
    Returns:
        Введенный текст или значение по умолчанию
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    
    if not value and default:
        return default
    
    return value


def confirm(prompt: str, default: bool = False) -> bool:
    """
    Запрос подтверждения у пользователя.
    
    Args:
        prompt: Текст вопроса
        default: Значение по умолчанию (True/False)
        
    Returns:
        True если пользователь подтвердил
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    
    while True:
        answer = input(prompt + suffix).strip().lower()
        
        if not answer:
            return default
        
        if answer in ('y', 'yes', 'да', 'д'):
            return True
        
        if answer in ('n', 'no', 'нет', 'н'):
            return False
        
        print_warning("Пожалуйста, введите y или n")
