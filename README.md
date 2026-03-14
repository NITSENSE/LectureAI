# Lecture Assistant 🎓

Автоматизированный ассистент для записи, транскрибации и обработки лекций с BigBlueButton.

## Возможности

- 📹 **Запись лекций** — автоматическое подключение к BBB-сессиям и запись аудио
- 🎙️ **Транскрибация** — преобразование аудио в текст через Uniscribe
- 🤖 **Генерация конспектов** — создание структурированных заметок с помощью Google Gemini
- ✂️ **Нарезка аудио** — разделение длинных записей на части по времени или размеру
- 📅 **Расписание** — управление расписанием лекций и автоматический запуск записи

## Структура проекта

```
Lecture Assistant/
├── main.py                 # Главная точка входа (CLI меню)
├── requirements.txt        # Зависимости Python
├── .env.example           # Шаблон переменных окружения
│
├── ai/                    # Модуль искусственного интеллекта
│   ├── gemini.py          # Интеграция с Google Gemini API
│   └── note_generator.py  # Генерация конспектов
│
├── audio/                 # Работа с аудио
│   └── chunker.py         # Нарезка аудиофайлов
│
├── config/                # Конфигурация
│   ├── settings.py        # Основные настройки
│   └── prompts.py         # Промпты для AI
│
├── core/                  # Основная логика
│   ├── recorder.py        # Запись с BBB
│   ├── transcriber.py     # Транскрибация
│   ├── processor.py       # Обработка лекций
│   └── scheduler.py       # Управление расписанием
│
├── data/                  # Данные и конфигурация
│   ├── links.json.example # Шаблон ссылок на лекции
│   └── paths.json.example # Шаблон путей к файлам
│
├── docs/                  # Документация
├── utils/                 # Утилиты
├── tests/                 # Тесты
└── scripts/               # Вспомогательные скрипты
```

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your-username/lecture-assistant.git
cd lecture-assistant
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните необходимые значения:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PROXY_URL=  # Опционально
```

### 5. Настроить пути и ссылки

```bash
cp data/paths.json.example data/paths.json
cp data/links.json.example data/links.json
```

Отредактируйте файлы согласно вашей системе:

**data/paths.json:**
```json
{
    "lectures_source": "/path/to/your/recordings",
    "chunks_to": "/path/to/output/chunks"
}
```

**data/links.json:**
```json
{
    "OperatingSystems": "https://bbb.example.com/b/xxx-yyy-zzz",
    "IOT": "https://bbb.example.com/b/aaa-bbb-ccc"
}
```

## Использование

### Запуск приложения

```bash
python main.py
```

### Основные функции

#### 1. Запись лекции
- Выберите лекцию из расписания или введите URL вручную
- Приложение автоматически подключится к BBB-сессии
- Аудио будет сохранено в `data/recordings/`

#### 2. Транскрибация
- Загрузите аудиофайл на Uniscribe
- Получите текстовую расшифровку
- Результат сохраняется рядом с исходным файлом

#### 3. Генерация конспектов
- На основе транскрипта создается структурированный конспект
- Используется Google Gemini для обработки текста
- Поддержка настраиваемых промптов

#### 4. Нарезка аудио
- Разделение по временным меткам
- Разделение по размеру файла
- Объединение нескольких частей

## Требования

- Python 3.9+
- Google Chrome (для записи BBB и транскрибации)
- FFmpeg (для обработки аудио)
- API ключ Google Gemini

## Переменные окружения

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `GEMINI_API_KEY` | API ключ Google Gemini | Да |
| `PROXY_URL` | URL прокси-сервера | Нет |

## Документация

Подробная документация по модулям находится в директории [`docs/`](docs/):

- [`docs/recorder.md`](docs/recorder.md) — модуль записи
- [`docs/transcriber.md`](docs/transcriber.md) — модуль транскрибации
- [`docs/processor.md`](docs/processor.md) — модуль обработки

## Лицензия

MIT License

