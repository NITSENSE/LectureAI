import os
import logging
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment
from pydub.utils import make_chunks
from moviepy import VideoFileClip

from config.settings import CHUNKS_DIR
from utils.file_ops import ensure_dir, get_file_size_mb
from utils.console import print_section, print_success, print_error, print_info

logger = logging.getLogger(__name__)


class AudioChunker:
    """
    Класс для нарезки аудио и видео файлов на аудио-части.
    """
    
    # Максимальный размер файла для транскрибации (в MB)
    MAX_FILE_SIZE_MB = 25
    
    # Длительность чанка по умолчанию: 30 минут (в миллисекундах)
    DEFAULT_CHUNK_LENGTH_MS = 30 * 60 * 1000  
    
    # Поддерживаемые видео-расширения для предварительного извлечения аудио
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv'}
    
    def __init__(
        self,
        output_dir: Path = CHUNKS_DIR,
        chunk_length_ms: int = DEFAULT_CHUNK_LENGTH_MS
    ):
        """
        Инициализация чанкера.
        
        Args:
            output_dir: Директория для сохранения чанков
            chunk_length_ms: Длительность одного чанка в миллисекундах
        """
        self.output_dir = output_dir
        self.chunk_length_ms = chunk_length_ms
        ensure_dir(output_dir)

    def _get_audio_segment(self, path: Path) -> Optional[AudioSegment]:
        """
        Приватный метод для безопасной загрузки аудио, в том числе из видеофайлов.
        """
        temp_audio_path = f"temp_{path.stem}_extracted.mp3"
        
        try:
            if path.suffix.lower() in self.VIDEO_EXTENSIONS:
                logger.info("Обнаружено видео. Извлекаю аудио во временный файл...")
                print_info("Извлечение аудио из видео...")
                
                # Извлекаем аудио во временный файл (pydub лучше работает с готовыми аудиофайлами)
                video = VideoFileClip(str(path))
                video.audio.write_audiofile(temp_audio_path, logger=None)
                video.close()
                
                audio = AudioSegment.from_file(temp_audio_path)
            else:
                logger.info(f"Загрузка аудиофайла: {path}")
                audio = AudioSegment.from_file(str(path))
                
            return audio
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке медиафайла: {e}")
            print_error(f"Ошибка чтения файла: {e}")
            return None
            
        finally:
            # Гарантированное удаление временного файла
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except OSError as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_audio_path}: {e}")

    def _export_chunks(self, audio: AudioSegment, original_path: Path, chunk_length_ms: int) -> List[Path]:
        """
        Приватный метод для нарезки и сохранения чанков.
        """
        chunk_dir = self.output_dir / original_path.stem
        ensure_dir(chunk_dir)
        
        chunks = make_chunks(audio, chunk_length_ms)
        logger.info(f"Создано чанков: {len(chunks)}")
        
        chunk_paths =[]
        
        for i, chunk in enumerate(chunks):
            chunk_name = f"part_{i+1}.mp3"
            chunk_path = chunk_dir / chunk_name
            
            # Экспорт чанка: bitrate="192k" (CBR) и -ar 44100 исправляют отображение времени в плеерах
            chunk.export(
                str(chunk_path),
                format="mp3",
                bitrate="192k",
                parameters=["-ar", "44100"] 
            )
            
            chunk_paths.append(chunk_path)
            logger.info(f"Создан чанк: {chunk_name} ({get_file_size_mb(chunk_path):.2f} MB)")
        
        print_success(f"Создано {len(chunk_paths)} чанков в {chunk_dir}")
        return chunk_paths
    
    def chunk_file(
        self,
        file_path: str | Path,
        chunk_length_ms: Optional[int] = None
    ) -> List[Path]:
        """
        Нарезка аудио/видео файла на части.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Файл не найден: {path}")
            return[]
        
        chunk_length = chunk_length_ms or self.chunk_length_ms
        
        print_section(f"НАРЕЗКА ФАЙЛА: {path.name}")
        print_info(f"Размер файла: {get_file_size_mb(path):.2f} MB")
        
        audio = self._get_audio_segment(path)
        if not audio:
            return[]
            
        return self._export_chunks(audio, path, chunk_length)
    
    def chunk_by_size(
        self,
        file_path: str | Path,
        max_size_mb: float = MAX_FILE_SIZE_MB
    ) -> List[Path]:
        """
        Нарезка файла на части определенного размера.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Файл не найден: {path}")
            return[]
        
        file_size_mb = get_file_size_mb(path)
        
        if file_size_mb <= max_size_mb:
            logger.info(f"Файл уже меньше {max_size_mb} MB, нарезка не требуется")
            return [path]
        
        print_section(f"НАРЕЗКА ПО РАЗМЕРУ: {path.name}")
        print_info(f"Размер файла: {file_size_mb:.2f} MB")
        print_info(f"Максимальный размер части: {max_size_mb} MB")
        
        audio = self._get_audio_segment(path)
        if not audio:
            return[]
            
        duration_ms = len(audio)
        
        # Расчет количества частей и длительности каждого чанка
        num_parts = int(file_size_mb / max_size_mb) + 1
        chunk_length_ms = duration_ms // num_parts
        
        logger.info(f"Длительность файла: {duration_ms / 1000:.1f} сек")
        logger.info(f"Длительность чанка: {chunk_length_ms / 1000:.1f} сек")
        
        return self._export_chunks(audio, path, chunk_length_ms)
    
    def merge_chunks(
        self,
        chunk_dir: str | Path,
        output_filename: str = "merged.mp3"
    ) -> Optional[Path]:
        """
        Объединение чанков в один файл.
        """
        dir_path = Path(chunk_dir)
        
        if not dir_path.exists():
            logger.error(f"Директория не найдена: {dir_path}")
            return None
        
        print_section(f"ОБЪЕДИНЕНИЕ ЧАНКОВ: {dir_path.name}")
        
        try:
            chunk_files = sorted(dir_path.glob("*.mp3"))
            
            if not chunk_files:
                logger.error("Чанки не найдены")
                return None
            
            logger.info(f"Найдено чанков: {len(chunk_files)}")
            merged = AudioSegment.empty()
            
            for chunk_file in chunk_files:
                logger.info(f"Добавление: {chunk_file.name}")
                chunk = AudioSegment.from_file(chunk_file)
                merged += chunk
            
            output_path = dir_path / output_filename
            
            # Добавлен параметр -ar 44100 и сюда для согласованности с частями
            merged.export(str(output_path), format="mp3", bitrate="192k", parameters=["-ar", "44100"])
            
            print_success(f"Объединенный файл: {output_path.name} ({get_file_size_mb(output_path):.2f} MB)")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при объединении чанков: {e}")
            print_error(f"Ошибка: {e}")
            return None
    
    def get_chunk_info(self, chunk_dir: str | Path) -> dict:
        """
        Получение информации о чанках в директории.
        """
        dir_path = Path(chunk_dir)
        
        if not dir_path.exists():
            return {"error": "Директория не найдена"}
        
        chunk_files = sorted(dir_path.glob("*.mp3"))
        
        if not chunk_files:
            return {"error": "Чанки не найдены"}
        
        total_size_mb = sum(get_file_size_mb(f) for f in chunk_files)
        
        return {
            "directory": str(dir_path),
            "num_chunks": len(chunk_files),
            "total_size_mb": round(total_size_mb, 2),
            "chunks":[
                {
                    "name": f.name,
                    "size_mb": round(get_file_size_mb(f), 2)
                }
                for f in chunk_files
            ]
        }