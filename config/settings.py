"""
Central configuration settings for Lecture Assistant.
All paths, API keys, and constants are defined here.
"""

import os
from pathlib import Path

# ==================== БАЗОВЫЕ ПУТИ ====================
BASE_DIR = Path(__file__).parent.parent.absolute()

# Директории данных
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
CHUNKS_DIR = DATA_DIR / "chunks"
SOURCE_DIR = BASE_DIR / "source"

# Файлы данных
LINKS_FILE = DATA_DIR / "links.json"
SCHEDULE_FILE = DATA_DIR / "schedule.json"
PATHS_FILE = DATA_DIR / "paths.json"

# ==================== BBB НАСТРОЙКИ ====================
BBB_USER_NAME = "Студент"
BBB_MIN_PARTICIPANTS = 5
BBB_HISTORY_SIZE = 60
BBB_CHECK_INTERVAL = 5  # секунд

# ==================== FFMPEG НАСТРОЙКИ ====================
FFMPEG_AUDIO_BITRATE = "192k"
FFMPEG_AUDIO_CODEC = "libmp3lame"

# ==================== UNISCRIBE НАСТРОЙКИ ====================
UNISCRIBE_URL = "https://www.uniscribe.co/ru"
UNISCRIBE_TIMEOUT = 300  # секунд
UNISCRIBE_MAX_RETRIES = 3

# XPaths для Uniscribe
UNISCRIBE_UPLOAD_BUTTON_XPATH = '//button[contains(text(), "Загрузите файл")]'
UNISCRIBE_START_BUTTON_XPATH = '//button[contains(., "Транскрибировать бесплатно")]'
UNISCRIBE_FILE_INPUT_XPATH = "//input[@type='file']"
UNISCRIBE_COPY_BUTTON_XPATH = "//*[local-name()='svg' and contains(@class, 'lucide-copy')]/ancestor::button"
UNISCRIBE_TRASH_BUTTON_XPATH = "//*[local-name()='svg' and contains(@class, 'lucide-trash2')]/ancestor::button"
UNISCRIBE_CONFIRM_DELETE_XPATH = '//button[contains(., "Удалить") and contains(@class, "bg-destructive")]'

# ==================== GEMINI НАСТРОЙКИ ====================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3-flash-preview"

# Прокси (если нужен)
PROXY_URL = os.environ.get("PROXY_URL", "")

# ==================== АУДИО НАСТРОЙКИ ====================
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.mp4', '.ogg'}
DEFAULT_RECORDING_FILENAME_TEMPLATE = "lecture_{timestamp}.mp3"

# ==================== ЛОГИРОВАНИЕ ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "lecture_assistant.log"

# Создаем директории если не существуют
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
