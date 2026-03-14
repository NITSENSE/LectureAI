"""
Lecture Assistant - Unified CLI Application
Main entry point with interactive menu.
"""

import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("lecture_assistant.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Импорты модулей
from config.settings import SOURCE_DIR, RECORDINGS_DIR
from utils.console import (
    print_header, print_section, print_success, print_error,
    print_warning, print_info, print_menu_item, get_input, confirm
)
from core.recorder import BBBRecorder
from core.scheduler import ScheduleManager
from core.transcriber import UniscribeTranscriber
from core.processor import LectureProcessor
from audio.chunker import AudioChunker
from ai.note_generator import NoteGenerator


def record_lecture_menu(processor: LectureProcessor) -> None:
    """Меню записи лекции."""
    print_header("ЗАПИСЬ ЛЕКЦИИ С BBB")
    
    scheduler = ScheduleManager()
    scheduler.display_available_lectures()
    
    if not scheduler.links:
        print_warning("Нет доступных лекций в links.json")
        url = get_input("Введите URL лекции BBB вручную")
        if not url:
            return
    else:
        lecture_key = get_input("Введите название лекции (ключ из links.json)")
        
        if lecture_key not in scheduler.links:
            print_error(f"Лекция '{lecture_key}' не найдена")
            return
        
        url = scheduler.links[lecture_key]
    
    user_name = get_input("Введите имя пользователя", "Студент")
    
    print_info(f"URL: {url}")
    print_info(f"Пользователь: {user_name}")
    
    if confirm("Начать запись?"):
        processor.record_lecture(url=url, user_name=user_name)


def transcribe_menu(processor: LectureProcessor) -> None:
    """Меню транскрибации."""
    print_header("ТРАНСКРИБАЦИЯ АУДИО")
    
    print_menu_item(1, "Транскрибировать один файл")
    print_menu_item(2, "Транскрибировать все pending файлы")
    print_menu_item(0, "Назад")
    
    choice = get_input("\nВаш выбор")
    
    if choice == "1":
        file_path = get_input("Введите путь к файлу")
        if file_path:
            processor.transcribe_file(file_path)
    elif choice == "2":
        processor.transcribe_pending_files(SOURCE_DIR)


def schedule_menu(scheduler: ScheduleManager) -> None:
    """Меню управления расписанием."""
    scheduler.run_interactive()


def chunking_menu() -> None:
    """Меню нарезки аудио."""
    print_header("НАРЕЗКА АУДИО")
    
    chunker = AudioChunker()
    
    print_menu_item(1, "Нарезать файл на части по времени")
    print_menu_item(2, "Нарезать файл по размеру")
    print_menu_item(3, "Объединить чанки")
    print_menu_item(0, "Назад")
    
    choice = get_input("\nВаш выбор")
    
    if choice == "1":
        file_path = get_input("Введите путь к файлу")
        if file_path:
            chunk_length = get_input("Длительность чанка (минуты)", "10")
            try:
                chunk_length_ms = int(chunk_length) * 60 * 1000
                chunker.chunk_file(file_path, chunk_length_ms)
            except ValueError:
                print_error("Неверный формат числа")
    elif choice == "2":
        file_path = get_input("Введите путь к файлу")
        if file_path:
            max_size = get_input("Максимальный размер части (MB)", "25")
            try:
                max_size_mb = float(max_size)
                chunker.chunk_by_size(file_path, max_size_mb)
            except ValueError:
                print_error("Неверный формат числа")
    elif choice == "3":
        chunk_dir = get_input("Введите путь к директории с чанками")
        if chunk_dir:
            chunker.merge_chunks(chunk_dir)


def notes_menu() -> None:
    """Меню генерации конспектов."""
    print_header("ГЕНЕРАЦИЯ КОНСПЕКТОВ")
    
    generator = NoteGenerator()
    
    print_menu_item(1, "Сгенерировать конспект из файла")
    print_menu_item(2, "Полная обработка лекции (конспект + резюме + термины + вопросы)")
    print_menu_item(0, "Назад")
    
    choice = get_input("\nВаш выбор")
    
    if choice == "1":
        file_path = get_input("Введите путь к файлу с транскрипцией")
        if file_path:
            generator.generate_notes_from_file(file_path)
    elif choice == "2":
        file_path = get_input("Введите путь к файлу с транскрипцией")
        if file_path:
            path = Path(file_path)
            if path.exists():
                text = path.read_text(encoding='utf-8')
                output_dir = path.parent / f"{path.stem}_ai"
                generator.process_lecture_complete(text, output_dir, path.stem)
            else:
                print_error("Файл не найден")


def main() -> None:
    """Главное меню приложения."""
    print_header("LECTURE ASSISTANT")
    print_info("Добро пожаловать в систему управления лекциями!")
    
    processor = LectureProcessor()
    scheduler = ScheduleManager()
    
    while True:
        print("\n" + "=" * 50)
        print_menu_item(1, "Записать лекцию (BBB)")
        print_menu_item(2, "Управление расписанием")
        print_menu_item(3, "Транскрибировать аудио")
        print_menu_item(4, "Нарезка аудио")
        print_menu_item(5, "Генерация конспектов (AI)")
        print_menu_item(6, "Показать следующую лекцию по расписанию")
        print_menu_item(0, "Выход")
        print("=" * 50)
        
        choice = get_input("\nВаш выбор")
        
        if choice == "1":
            record_lecture_menu(processor)
        elif choice == "2":
            schedule_menu(scheduler)
        elif choice == "3":
            transcribe_menu(processor)
        elif choice == "4":
            chunking_menu()
        elif choice == "5":
            notes_menu()
        elif choice == "6":
            next_lecture = scheduler.get_next_lecture()
            if next_lecture:
                day_ru = ScheduleManager.DAYS_RU.get(next_lecture["day"], next_lecture["day"])
                print_info(f"Следующая лекция: {next_lecture['lecture']}")
                print_info(f"Время: {day_ru} {next_lecture['time']}")
            else:
                print_info("Нет запланированных лекций")
        elif choice == "0":
            print_info("До свидания!")
            break
        else:
            print_error("Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\nПрограмма остановлена пользователем")
    except Exception as e:
        logger.exception("Критическая ошибка")
        print_error(f"Критическая ошибка: {e}")
        sys.exit(1)
