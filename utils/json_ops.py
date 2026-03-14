"""
JSON file operations.
Refactored from json_operations.py
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def read_json(path_to_json: str | Path) -> Dict[str, Any]:
    """
    Загружает данные из JSON-файла и возвращает их в виде словаря.
    
    Args:
        path_to_json: Путь к JSON-файлу
        
    Returns:
        Словарь с данными из JSON
        
    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если файл содержит невалидный JSON
    """
    path = Path(path_to_json)
    
    if not path.exists():
        raise FileNotFoundError(f"JSON файл не найден: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Ошибка парсинга JSON: {e}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"Ошибка при чтении JSON файла: {e}")


def write_json(path_to_json: str | Path, data: Dict[str, Any], indent: int = 4) -> bool:
    """
    Сохраняет данные в JSON-файл.
    
    Args:
        path_to_json: Путь к JSON-файлу
        data: Данные для сохранения
        indent: Отступ для форматирования
        
    Returns:
        True если успешно, иначе False
    """
    path = Path(path_to_json)
    
    try:
        # Создаем директорию если не существует
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"Ошибка при записи JSON файла: {e}")
        return False


def read_file(path_to_file: str | Path) -> str:
    """
    Читает содержимое текстового файла.
    
    Args:
        path_to_file: Путь к файлу
        
    Returns:
        Содержимое файла
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    path = Path(path_to_file)
    
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла: {e}")


def write_file(path_to_file: str | Path, content: str) -> bool:
    """
    Записывает содержимое в текстовый файл.
    
    Args:
        path_to_file: Путь к файлу
        content: Содержимое для записи
        
    Returns:
        True если успешно, иначе False
    """
    path = Path(path_to_file)
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        return False
