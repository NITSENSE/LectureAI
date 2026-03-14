import os
from pathlib import Path
from typing import List, Optional, Set


def find_files(
    directory: str | Path,
    extensions: Optional[Set[str]] = None,
    recursive: bool = True
) -> List[Path]:
    """
    Поиск файлов в директории с фильтрацией по расширениям.
    
    Args:
        directory: Директория для поиска
        extensions: Множество расширений для фильтрации (например, {'.mp3', '.wav'})
        recursive: Рекурсивный поиск
        
    Returns:
        Список путей к найденным файлам
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    files = []
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in extensions:
                files.append(file_path)
    
    return sorted(files)


def find_files_without_counterpart(
    directory: str | Path,
    source_ext: Set[str],
    counterpart_ext: str,
    recursive: bool = True
) -> List[Path]:
    """
    Поиск файлов, у которых нет соответствующего файла-аналога.
    
    Пример: найти .mp3 файлы, у которых нет .txt файла
    
    Args:
        directory: Директория для поиска
        source_ext: Расширения исходных файлов
        counterpart_ext: Расширение файла-аналога
        recursive: Рекурсивный поиск
        
    Returns:
        Список путей к файлам без аналога
    """
    files = find_files(directory, source_ext, recursive)
    
    files_without_counterpart = []
    
    for file_path in files:
        counterpart_path = file_path.with_suffix(counterpart_ext)
        if not counterpart_path.exists():
            files_without_counterpart.append(file_path)
    
    return files_without_counterpart


def get_file_size(file_path: str | Path) -> int:
    """
    Получение размера файла в байтах.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Размер файла в байтах, 0 если файл не найден
    """
    path = Path(file_path)
    
    if path.exists():
        return path.stat().st_size
    
    return 0


def get_file_size_mb(file_path: str | Path) -> float:
    """
    Получение размера файла в мегабайтах.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Размер файла в мегабайтах
    """
    return get_file_size(file_path) / (1024 * 1024)


def ensure_dir(directory: str | Path) -> Path:
    """
    Создает директорию если она не существует.
    
    Args:
        directory: Путь к директории
        
    Returns:
        Path объект директории
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_unique_filename(directory: str | Path, base_name: str, extension: str) -> Path:
    """
    Генерация уникального имени файла.
    Если файл уже существует, добавляет суффикс _1, _2, и т.д.
    
    Args:
        directory: Директория
        base_name: Базовое имя файла
        extension: Расширение файла
        
    Returns:
        Уникальный путь к файлу
    """
    dir_path = Path(directory)
    counter = 0
    
    while True:
        if counter == 0:
            filename = f"{base_name}{extension}"
        else:
            filename = f"{base_name}_{counter}{extension}"
        
        file_path = dir_path / filename
        
        if not file_path.exists():
            return file_path
        
        counter += 1
