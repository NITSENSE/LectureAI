# core/processor.py — Документация

## Обзор

[`core/processor.py`](../core/processor.py) — это **оркестратор** (фасад) для обработки лекций. Он объединяет три основных этапа:

1. **Запись** лекций с BigBlueButton (BBB)
2. **Транскрибация** аудио через сервис Uniscribe
3. **Управление расписанием** лекций

Класс [`LectureProcessor`](../core/processor.py:27) делегирует работу специализированным модулям, предоставляя единый интерфейс для всех операций.

---

## Класс LectureProcessor

### Конструктор `__init__`

```python
def __init__(
    self,
    headless: bool = False,
    max_wait: int = 300,
    min_participants: int = 5,
    history_size: int = 60,
    check_interval: int = 5
)
```

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `headless` | `bool` | `False` | Запуск браузера в фоновом режиме (без GUI) |
| `max_wait` | `int` | `300` | Максимальное время ожидания (секунды) |
| `min_participants` | `int` | `5` | Минимальное количество участников для записи |
| `history_size` | `int` | `60` | Размер истории участников |
| `check_interval` | `int` | `5` | Интервал проверки состояния (секунды) |

При инициализации создаётся экземпляр [`ScheduleManager`](../core/scheduler.py:22) для работы с расписанием.

---

## Методы

### 1. `record_lecture` — Запись лекции с BBB

```python
def record_lecture(
    self,
    url: str,
    user_name: str = "Студент",
    filename: Optional[str] = None
) -> Optional[Path]
```

**Описание:** Записывает лекцию с BigBlueButton, используя [`BBBRecorder`](../core/recorder.py).

**Алгоритм:**
1. Создаёт экземпляр [`BBBRecorder`](../core/recorder.py) с переданными параметрами
2. Вызывает [`recorder.start_session()`](../core/recorder.py) для начала записи
3. При успешной записи — возвращает путь к файлу и выводит его размер
4. При `KeyboardInterrupt` — останавливает запись и возвращает частично записанный файл
5. При ошибке — логирует и возвращает `None`

**Возвращает:** `Path` к записанному файлу или `None`

---

### 2. `transcribe_file` — Транскрибация одного файла

```python
def transcribe_file(
    self,
    file_path: str | Path,
    delete_from_server: bool = True
) -> Optional[str]
```

**Описание:** Транскрибирует один аудиофайл через сервис Uniscribe.

**Алгоритм:**
1. Для каждой попытки (до `UNISCRIBE_MAX_RETRIES = 3`):
   - Создаёт контекстный менеджер [`UniscribeTranscriber`](../core/transcriber.py:33)
   - Вызывает [`transcriber.transcribe(path, delete_from_server)`](../core/transcriber.py)
   - При успехе — сохраняет текст в `.txt` файл с тем же именем
2. Если все попытки неудачны — возвращает `None`

**Возвращает:** Текст транскрипции или `None`

---

### 3. `transcribe_pending_files` — Транскрибация всех ожидающих файлов

```python
def transcribe_pending_files(
    self,
    directory: str | Path = SOURCE_DIR
) -> dict
```

**Описание:** Находит все аудиофайлы без соответствующих `.txt` файлов и транскрибирует их.

**Алгоритм:**
1. Использует [`find_files_without_counterpart()`](../utils/file_ops.py:47) для поиска файлов без транскрипции
2. Создаёт один экземпляр [`UniscribeTranscriber`](../core/transcriber.py:33) для всех файлов (оптимизация)
3. Для каждого файла:
   - Пытается транскрибировать (до `UNISCRIBE_MAX_RETRIES` попыток)
   - Сохраняет результат в `.txt` файл
4. Выводит итоговую статистику

**Возвращает:** Словарь `{имя_файла: текст_транскрипции}`

---

### 4. `process_scheduled_lecture` — Обработка лекции по расписанию

```python
def process_scheduled_lecture(self) -> Optional[Path]
```

**Описание:** Записывает следующую запланированную лекцию согласно расписанию.

**Алгоритм:**
1. Получает следующую лекцию через [`scheduler.get_next_lecture()`](../core/scheduler.py)
2. Если лекций нет — выводит сообщение и возвращает `None`
3. Ищет URL лекции в [`links.json`](../data/links.json) через [`scheduler.links`](../core/scheduler.py)
4. Если URL не найден — выводит ошибку и возвращает `None`
5. Вызывает [`record_lecture()`](../core/processor.py:59) для записи

**Возвращает:** `Path` к записанному файлу или `None`

---

## Зависимости

### Стандартная библиотека Python

| Модуль | Использование |
|--------|---------------|
| `logging` | Логирование ошибок и информационных сообщений |
| `pathlib.Path` | Работа с файловыми путями |
| `typing` | Аннотации типов (`Optional`, `List`) |

### Внутренние модули проекта

#### config/settings.py

Импортируемые константы:

| Константа | Значение | Описание |
|-----------|----------|----------|
| [`RECORDINGS_DIR`](../config/settings.py:14) | `data/recordings` | Директория для записей |
| [`CHUNKS_DIR`](../config/settings.py:15) | `data/chunks` | Директория для чанков |
| [`SOURCE_DIR`](../config/settings.py:16) | `source` | Директория исходных файлов |
| [`AUDIO_EXTENSIONS`](../config/settings.py:54) | `{'.mp3', '.wav', '.m4a', '.mp4', '.ogg'}` | Поддерживаемые расширения аудио |
| [`UNISCRIBE_MAX_RETRIES`](../config/settings.py:36) | `3` | Максимум попыток транскрибации |

#### utils/file_ops.py

| Функция | Описание |
|---------|----------|
| [`find_files_without_counterpart()`](../utils/file_ops.py:47) | Поиск файлов без соответствующего файла-аналога (например, `.mp3` без `.txt`) |
| [`get_file_size_mb()`](../utils/file_ops.py:97) | Получение размера файла в мегабайтах |

#### utils/console.py

| Функция | Описание |
|---------|----------|
| [`print_header()`](../utils/console.py:56) | Печать заголовка с рамкой |
| [`print_section()`](../utils/console.py:69) | Печать заголовка секции |
| [`print_success()`](../utils/console.py:79) | Печать сообщения об успехе (зелёный) |
| [`print_error()`](../utils/console.py:89) | Печать сообщения об ошибке (красный) |
| [`print_info()`](../utils/console.py) | Печать информационного сообщения |

#### core/recorder.py

| Класс | Описание |
|-------|----------|
| [`BBBRecorder`](../core/recorder.py) | Запись лекций с BigBlueButton через Selenium и FFmpeg |

#### core/scheduler.py

| Класс | Описание |
|-------|----------|
| [`ScheduleManager`](../core/scheduler.py:22) | Управление расписанием лекций и ссылками |

#### core/transcriber.py

| Класс | Описание |
|-------|----------|
| [`UniscribeTranscriber`](../core/transcriber.py:33) | Транскрибация аудио через сервис Uniscribe (Selenium + undetected-chromedriver) |

---

## Схема зависимостей

```
core/processor.py
├── config/settings.py
│   ├── RECORDINGS_DIR
│   ├── CHUNKS_DIR
│   ├── SOURCE_DIR
│   ├── AUDIO_EXTENSIONS
│   └── UNISCRIBE_MAX_RETRIES
├── utils/file_ops.py
│   ├── find_files_without_counterpart()
│   └── get_file_size_mb()
├── utils/console.py
│   ├── print_header()
│   ├── print_section()
│   ├── print_success()
│   ├── print_error()
│   └── print_info()
├── core/recorder.py
│   └── BBBRecorder
├── core/scheduler.py
│   └── ScheduleManager
└── core/transcriber.py
    └── UniscribeTranscriber
```

---

## Внешние зависимости (requirements.txt)

Для работы модулей, используемых `processor.py`, требуются:

| Пакет | Используется в | Назначение |
|-------|----------------|------------|
| `selenium` | [`recorder.py`](../core/recorder.py), [`transcriber.py`](../core/transcriber.py) | Автоматизация браузера |
| `undetected-chromedriver` | [`transcriber.py`](../core/transcriber.py) | Обход защиты от ботов |
| `webdriver-manager` | [`recorder.py`](../core/recorder.py) | Автоматическая установка ChromeDriver |
| `ffmpeg` (системный) | [`recorder.py`](../core/recorder.py) | Запись и обработка аудио |

---

## Примеры использования

### Запись лекции

```python
from core.processor import LectureProcessor

processor = LectureProcessor(headless=True)
recorded_file = processor.record_lecture(
    url="https://bbb.example.com/room/abc123",
    user_name="Студент"
)
```

### Транскрибация одного файла

```python
processor = LectureProcessor(headless=True)
text = processor.transcribe_file("source/lecture_20240101.mp3")
```

### Транскрибация всех ожидающих файлов

```python
processor = LectureProcessor(headless=True)
results = processor.transcribe_pending_files()
# results = {"lecture1.mp3": "текст...", "lecture2.mp3": "текст..."}
```

### Обработка лекции по расписанию

```python
processor = LectureProcessor()
recorded_file = processor.process_scheduled_lecture()
```

---

## Обработка ошибок

Модуль использует многоуровневую обработку ошибок:

1. **`KeyboardInterrupt`** — корректная остановка записи при прерывании пользователем
2. **Повторные попытки** — до 3 попыток транскрибации при сбоях
3. **Логирование** — все ошибки записываются через `logging`
4. **Визуальные сообщения** — пользователь видит цветные сообщения об успехе/ошибке

---

## Архитектурные решения

### Паттерн Фасад

[`LectureProcessor`](../core/processor.py:27) реализует паттерн **Facade**, предоставляя простой интерфейс для сложных операций, которые涉及多个子系统.

### Контекстные менеджеры

Транскрибер используется как контекстный менеджер (`with ... as transcriber:`), что гарантирует корректное закрытие браузера даже при ошибках.

### Конфигурация через константы

Все настройки вынесены в [`config/settings.py`](../config/settings.py), что упрощает изменение параметров без модификации кода.
