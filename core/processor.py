import logging
from pathlib import Path
from typing import Optional, List

from config.settings import (
    RECORDINGS_DIR,
    CHUNKS_DIR,
    SOURCE_DIR,
    AUDIO_EXTENSIONS,
    UNISCRIBE_MAX_RETRIES
)
from utils.file_ops import find_files_without_counterpart, get_file_size_mb
from utils.console import print_header, print_section, print_success, print_error, print_info

from core.recorder import BBBRecorder
from core.scheduler import ScheduleManager
from core.transcriber import UniscribeTranscriber

logger = logging.getLogger(__name__)


class LectureProcessor:
    """
    Единый класс для обработки лекций: запись, нарезка, транскрибация.
    Делегирует работу специализированным модулям.
    """
    
    def __init__(
        self,
        headless: bool = False,
        max_wait: int = 300,
        min_participants: int = 5,
        history_size: int = 60,
        check_interval: int = 5
    ):
        """
        Инициализация процессора лекций.
        
        Args:
            headless: Запуск браузера в фоновом режиме
            max_wait: Максимальное время ожидания
            min_participants: Минимальное количество участников
            history_size: Размер истории участников
            check_interval: Интервал проверки
        """
        self.headless = headless
        self.max_wait = max_wait
        self.min_participants = min_participants
        self.history_size = history_size
        self.check_interval = check_interval
        
        self.scheduler = ScheduleManager()
    
    def record_lecture(
        self,
        url: str,
        user_name: str = "Студент",
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Запись лекции с BBB.
        
        Args:
            url: URL лекции BBB
            user_name: Имя пользователя
            filename: Имя файла для записи
            
        Returns:
            Путь к записанному файлу или None
        """
        print_section("ЗАПИСЬ ЛЕКЦИИ С BBB")
        
        recorder = BBBRecorder(
            url=url,
            user_name=user_name,
            min_participants=self.min_participants,
            history_size=self.history_size,
            check_interval=self.check_interval,
            filename=filename
        )
        
        try:
            recorded_file = recorder.start_session()
            
            if recorded_file and recorded_file.exists():
                size_mb = get_file_size_mb(recorded_file)
                print_success(f"Лекция записана: {recorded_file.name} ({size_mb:.2f} MB)")
                return recorded_file
            else:
                print_error("Не удалось записать лекцию")
                return None
                
        except KeyboardInterrupt:
            print_info("Запись остановлена пользователем")
            return recorder.audio_recorder.stop()
        except Exception as e:
            logger.error(f"Ошибка при записи лекции: {e}")
            print_error(f"Ошибка: {e}")
            return None
    
    def transcribe_file(
        self,
        file_path: str | Path,
        delete_from_server: bool = True
    ) -> Optional[str]:
        """
        Транскрибация одного файла.
        
        Args:
            file_path: Путь к аудио файлу
            delete_from_server: Удалить файл с сервера после транскрибации
            
        Returns:
            Текст транскрипции или None
        """
        path = Path(file_path)
        print_section(f"ТРАНСКРИБАЦИЯ: {path.name}")
        
        for attempt in range(1, UNISCRIBE_MAX_RETRIES + 1):
            logger.info(f"Попытка {attempt}/{UNISCRIBE_MAX_RETRIES}")
            
            try:
                with UniscribeTranscriber(
                    headless=self.headless,
                    max_wait=self.max_wait
                ) as transcriber:
                    text = transcriber.transcribe(path, delete_from_server)
                    
                    if text:
                        # Сохраняем результат
                        txt_path = path.with_suffix(".txt")
                        txt_path.write_text(text, encoding="utf-8")
                        print_success(f"Транскрипция сохранена: {txt_path.name}")
                        return text
                    else:
                        print_error(f"Попытка {attempt}: не удалось получить текст")
                        
            except Exception as e:
                logger.error(f"Ошибка при попытке {attempt}: {e}")
                print_error(f"Ошибка: {e}")
        
        print_error(f"Не удалось транскрибировать после {UNISCRIBE_MAX_RETRIES} попыток")
        return None
    
    def transcribe_pending_files(
        self,
        directory: str | Path = SOURCE_DIR
    ) -> dict:
        """
        Транскрибация всех файлов, у которых нет .txt файла.
        
        Args:
            directory: Директория с файлами
            
        Returns:
            Словарь {имя_файла: текст_транскрипции}
        """
        print_header("ТРАНСКРИБАЦИЯ ОЖИДАЮЩИХ ФАЙЛОВ")
        
        # Находим файлы без транскрипции
        files_to_process = find_files_without_counterpart(
            directory=directory,
            source_ext=AUDIO_EXTENSIONS,
            counterpart_ext=".txt"
        )
        
        if not files_to_process:
            print_info("Все файлы уже обработаны или аудиофайлы не найдены.")
            return {}
        
        print_info(f"Найдено файлов для обработки: {len(files_to_process)}")
        
        results = {}
        
        with UniscribeTranscriber(
            headless=self.headless,
            max_wait=self.max_wait
        ) as transcriber:
            for file_path in files_to_process:
                print_section(f"Обработка: {file_path.name}")
                
                success = False
                for attempt in range(1, UNISCRIBE_MAX_RETRIES + 1):
                    logger.info(f"Попытка {attempt}/{UNISCRIBE_MAX_RETRIES}")
                    
                    try:
                        text = transcriber.transcribe(file_path)
                        
                        if text:
                            # Сохраняем результат
                            txt_path = file_path.with_suffix(".txt")
                            txt_path.write_text(text, encoding="utf-8")
                            print_success(f"Сохранено: {txt_path.name}")
                            results[file_path.name] = text
                            success = True
                            break
                        else:
                            print_error(f"Попытка {attempt}: не удалось получить текст")
                            
                    except Exception as e:
                        logger.error(f"Ошибка при попытке {attempt}: {e}")
                        print_error(f"Ошибка: {e}")
                
                if not success:
                    print_error(f"Файл {file_path.name} не удалось обработать")
        
        print_section("ИТОГИ")
        print_success(f"Обработано файлов: {len(results)}")
        print_error(f"Не удалось обработать: {len(files_to_process) - len(results)}")
        
        return results
    
    def process_scheduled_lecture(self) -> Optional[Path]:
        """
        Обработка следующей лекции по расписанию.
        
        Returns:
            Путь к записанному файлу или None
        """
        print_header("ОБРАБОТКА ЛЕКЦИИ ПО РАСПИСАНИЮ")
        
        next_lecture = self.scheduler.get_next_lecture()
        
        if not next_lecture:
            print_info("Нет запланированных лекций")
            return None
        
        lecture_name = next_lecture["lecture"]
        day = ScheduleManager.DAYS_RU.get(next_lecture["day"], next_lecture["day"])
        time = next_lecture["time"]
        
        print_info(f"Следующая лекция: {lecture_name}")
        print_info(f"Время: {day} {time}")
        
        # Получаем URL из links.json
        if lecture_name not in self.scheduler.links:
            print_error(f"URL для лекции '{lecture_name}' не найден в links.json")
            return None
        
        url = self.scheduler.links[lecture_name]
        
        # Записываем лекцию
        return self.record_lecture(url=url, user_name="Студент")
