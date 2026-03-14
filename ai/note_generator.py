import logging
from pathlib import Path
from typing import Optional

from config.prompts import (
    LECTURE_NOTE_PROMPT,
    SUMMARY_PROMPT,
    KEY_TERMS_PROMPT,
    QUIZ_PROMPT
)
from utils.json_ops import read_file, write_file
from utils.console import print_section, print_success, print_error, print_info

from .gemini import GeminiClient

logger = logging.getLogger(__name__)


class NoteGenerator:
    """
    Генератор конспектов лекций с использованием AI.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3-flash-preview"
    ):
        """
        Инициализация генератора конспектов.
        
        Args:
            api_key: API ключ Gemini
            model_name: Название модели
        """
        self.client = GeminiClient(api_key=api_key, model_name=model_name)
    
    def generate_notes(
        self,
        text: str,
        output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Генерация конспекта лекции.
        
        Args:
            text: Текст лекции
            output_path: Путь для сохранения (опционально)
            
        Returns:
            Сгенерированный конспект или None
        """
        print_section("ГЕНЕРАЦИЯ КОНСПЕКТА")
        print_info(f"Длина текста: {len(text)} символов")
        
        prompt = LECTURE_NOTE_PROMPT.format(text=text)
        notes = self.client.generate(prompt)
        
        if notes:
            print_success(f"Конспект сгенерирован ({len(notes)} символов)")
            
            if output_path:
                if write_file(output_path, notes):
                    print_success(f"Конспект сохранен: {output_path}")
            
            return notes
        else:
            print_error("Не удалось сгенерировать конспект")
            return None
    
    def generate_notes_from_file(
        self,
        file_path: str | Path,
        output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Генерация конспекта из файла с транскрипцией.
        
        Args:
            file_path: Путь к файлу с транскрипцией
            output_path: Путь для сохранения (если None, используется имя_файла_notes.md)
            
        Returns:
            Сгенерированный конспект или None
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Файл не найден: {path}")
            return None
        
        # Определяем путь для сохранения
        if output_path is None:
            output_path = path.parent / f"{path.stem}_notes.md"
        
        try:
            text = read_file(path)
            return self.generate_notes(text, output_path)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            return None
    
    def generate_summary(self, text: str) -> Optional[str]:
        """
        Генерация краткого резюме.
        
        Args:
            text: Текст лекции
            
        Returns:
            Краткое резюме или None
        """
        print_section("ГЕНЕРАЦИЯ РЕЗЮМЕ")
        
        prompt = SUMMARY_PROMPT.format(text=text)
        summary = self.client.generate(prompt)
        
        if summary:
            print_success(f"Резюме сгенерировано ({len(summary)} символов)")
            return summary
        else:
            print_error("Не удалось сгенерировать резюме")
            return None
    
    def extract_key_terms(self, text: str) -> Optional[str]:
        """
        Извлечение ключевых терминов.
        
        Args:
            text: Текст лекции
            
        Returns:
            Ключевые термины или None
        """
        print_section("ИЗВЛЕЧЕНИЕ КЛЮЧЕВЫХ ТЕРМИНОВ")
        
        prompt = KEY_TERMS_PROMPT.format(text=text)
        terms = self.client.generate(prompt)
        
        if terms:
            print_success(f"Термины извлечены ({len(terms)} символов)")
            return terms
        else:
            print_error("Не удалось извлечь термины")
            return None
    
    def generate_quiz(self, text: str) -> Optional[str]:
        """
        Генерация вопросов для самопроверки.
        
        Args:
            text: Текст лекции
            
        Returns:
            Вопросы для самопроверки или None
        """
        print_section("ГЕНЕРАЦИЯ ВОПРОСОВ ДЛЯ САМОПРОВЕРКИ")
        
        prompt = QUIZ_PROMPT.format(text=text)
        quiz = self.client.generate(prompt)
        
        if quiz:
            print_success(f"Вопросы сгенерированы ({len(quiz)} символов)")
            return quiz
        else:
            print_error("Не удалось сгенерировать вопросы")
            return None
    
    def process_lecture_complete(
        self,
        text: str,
        output_dir: Path,
        lecture_name: str = "lecture"
    ) -> dict:
        """
        Полная обработка лекции: конспект + резюме + термины + вопросы.
        
        Args:
            text: Текст лекции
            output_dir: Директория для сохранения
            lecture_name: Название лекции
            
        Returns:
            Словарь с результатами
        """
        print_section(f"ПОЛНАЯ ОБРАБОТКА ЛЕКЦИИ: {lecture_name}")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Конспект
        notes = self.generate_notes(text, output_dir / f"{lecture_name}_notes.md")
        results["notes"] = notes
        
        # Резюме
        summary = self.generate_summary(text)
        if summary:
            summary_path = output_dir / f"{lecture_name}_summary.md"
            write_file(summary_path, summary)
            results["summary"] = summary
        
        # Ключевые термины
        terms = self.extract_key_terms(text)
        if terms:
            terms_path = output_dir / f"{lecture_name}_terms.md"
            write_file(terms_path, terms)
            results["terms"] = terms
        
        # Вопросы
        quiz = self.generate_quiz(text)
        if quiz:
            quiz_path = output_dir / f"{lecture_name}_quiz.md"
            write_file(quiz_path, quiz)
            results["quiz"] = quiz
        
        print_section("ИТОГИ ОБРАБОТКИ")
        print_success(f"Создано файлов: {len([v for v in results.values() if v])}")
        
        return results
