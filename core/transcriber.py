"""
Uniscribe Transcriber.
Refactored and hardened for production headless environments.
"""

import time
import random
import logging
from pathlib import Path
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc

from config.settings import (
    UNISCRIBE_URL,
    UNISCRIBE_TIMEOUT,
    UNISCRIBE_MAX_RETRIES,
    UNISCRIBE_UPLOAD_BUTTON_XPATH,
    UNISCRIBE_START_BUTTON_XPATH,
    UNISCRIBE_FILE_INPUT_XPATH,
    UNISCRIBE_COPY_BUTTON_XPATH,
    UNISCRIBE_TRASH_BUTTON_XPATH,
    UNISCRIBE_CONFIRM_DELETE_XPATH,
)

logger = logging.getLogger(__name__)


class UniscribeTranscriber:
    """
    Класс для автоматизации транскрибации аудио через сервис Uniscribe.
    Поддерживает headless-режим и надежный перехват текста через JavaScript.
    """

    def __init__(
        self,
        headless: bool = False,
        proxy: Optional[str] = None,
        max_wait: int = UNISCRIBE_TIMEOUT
    ):
        """
        Инициализация транскрайбера.
        
        Args:
            headless: Запуск браузера в фоновом режиме
            proxy: URL прокси (опционально)
            max_wait: Максимальное время ожидания (секунды)
        """
        self.headless = headless
        self.proxy = proxy or None
        self.max_wait = max_wait
        self.driver = None

    def __enter__(self):
        """Для использования с оператором with."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из with."""
        self.quit()

    def start_browser(self) -> None:
        """Запуск браузера Chrome (undetected)."""
        if self.driver:
            return

        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            
            if self.headless:
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
            
            if self.proxy:
                options.add_argument(f'--proxy-server={self.proxy}')
            
            self.driver = uc.Chrome(options=options, use_subprocess=True, version_main=145)
            logger.info("Браузер запущен")
            
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера: {e}")
            raise

    def quit(self) -> None:
        """Полная очистка и закрытие браузера."""
        if self.driver:
            try:
                self._clean_web_data()
                self.driver.quit()
                logger.info("Браузер закрыт")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии браузера: {e}")
            finally:
                self.driver = None

    def _clean_web_data(self) -> None:
        """Очистка куки и хранилища для избежания накопления сессий."""
        if not self.driver: 
            return
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        except:
            pass

    def _click_safely(self, element) -> None:
        """Нажимает на элемент через JS, если обычный клик перекрыт."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
        except (WebDriverException, Exception):
            self.driver.execute_script("arguments[0].click();", element)

    def _delete_file(self) -> bool:
        """Находит и удаляет текущий файл на сайте, чтобы освободить место."""
        try:
            wait = WebDriverWait(self.driver, 5)
            
            trash_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, UNISCRIBE_TRASH_BUTTON_XPATH))
            )
            self._click_safely(trash_btn)
            
            confirm_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, UNISCRIBE_CONFIRM_DELETE_XPATH))
            )
            self._click_safely(confirm_btn)
            
            # Ждем появления кнопки загрузки (признак того, что сайт готов к новому файлу)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, UNISCRIBE_UPLOAD_BUTTON_XPATH))
            )
            logger.info("Файл удален с сервера.")
            return True
        except TimeoutException:
            # Если корзины нет, значит файлов нет, всё в порядке
            return False
        except Exception as e:
            logger.warning(f"Не удалось удалить файл с сервера: {e}")
            return False

    def _extract_text(self, copy_btn) -> Optional[str]:
        """
        Извлечение текста транскрипции через перехват буфера обмена JS.
        Надежно работает в headless среде (в отличие от pyperclip).
        """
        try:
            self.driver.execute_script("""
                window.myBotClipboard = "";
                navigator.clipboard.writeText = function(text) {
                    window.myBotClipboard = text;
                    return Promise.resolve();
                };
            """)
            
            self._click_safely(copy_btn)

            # Читаем переменную из браузера
            content = ""
            for _ in range(20):  # Ждем до 10 секунд
                content = self.driver.execute_script("return window.myBotClipboard;")
                if content and len(content) > 5:
                    return content
                time.sleep(0.5)

            logger.warning("Не удалось извлечь текст из буфера браузера.")
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста: {e}")
            return None

    def transcribe(
        self,
        file_path: str | Path,
        delete_after: bool = True
    ) -> Optional[str]:
        """
        Основной метод: загружает файл, ждет транскрибацию и возвращает текст.
        
        Args:
            file_path: Путь к аудио файлу
            delete_after: Удалить файл с сервера после транскрибации
            
        Returns:
            Текст транскрипции или None
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Файл не найден: {path}")
            return None
        
        if not self.driver:
            self.start_browser()
        
        try:
            logger.info(f"Транскрибация файла: {path.name}")
            
            # Переход на сайт
            self.driver.get(UNISCRIBE_URL)
            time.sleep(random.uniform(2, 3))
            
            # 0. Очистка старых файлов перед загрузкой (защита от зависаний)
            self._delete_file()
            
            wait = WebDriverWait(self.driver, self.max_wait)
            
            # 1. Загрузка файла
            logger.info("Загрузка файла...")
            wait.until(
                EC.presence_of_element_located((By.XPATH, UNISCRIBE_UPLOAD_BUTTON_XPATH))
            )
            file_input = self.driver.find_element(By.XPATH, UNISCRIBE_FILE_INPUT_XPATH)
            file_input.send_keys(str(path.absolute()))
            time.sleep(2)
            
            # 2. Ожидание и нажатие кнопки начала транскрибации
            logger.info("Ожидание кнопки транскрибации...")
            start_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, UNISCRIBE_START_BUTTON_XPATH))
            )
            self._click_safely(start_btn)
            
            # 3. Ожидание завершения транскрибации
            logger.info(f"Ожидание результата (лимит {self.max_wait} сек)...")
            copy_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, UNISCRIBE_COPY_BUTTON_XPATH))
            )
            logger.info("Готово! Извлекаем текст...")
            time.sleep(2)  # Зазор для рендера текста внутри скрытых блоков сайта
            
            # 4. Извлечение текста через JS
            text = self._extract_text(copy_btn)
            
            # 5. Удаление файла с сервера
            if delete_after:
                self._delete_file()
            
            length = len(text) if text else 0
            logger.info(f"Транскрибация завершена: {length} символов")
            
            return text
            
        except TimeoutException:
            logger.error("Превышено время ожидания (TimeoutException)")
            return None
        except Exception as e:
            logger.error(f"Ошибка при обработке {path.name}: {e}")
            return None

    def transcribe_batch(
        self,
        file_paths: List[str | Path],
        delete_after: bool = True
    ) -> dict:
        """
        Транскрибация нескольких файлов.
        
        Args:
            file_paths: Список путей к файлам
            delete_after: Удалить файлы с сервера после транскрибации
            
        Returns:
            Словарь {путь_к_файлу: текст_транскрипции}
        """
        results = {}
        
        for file_path in file_paths:
            path = Path(file_path)
            text = self.transcribe(path, delete_after)
            results[str(path)] = text
            
            # Пауза между запросами для симуляции реального пользователя
            time.sleep(random.uniform(2, 5))
        
        return results

# ==========================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ (для локальных тестов)
# ==========================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    # Чтобы запустить тест, можно закомментировать импорты из config.settings
    # и объявить константы прямо здесь
    
    test_file = Path("test_audio.mp3")
    
    if test_file.exists():
        with UniscribeTranscriber(headless=True) as worker:
            result = worker.transcribe(test_file)
            if result:
                print("\n--- РЕЗУЛЬТАТ ---")
                print(result[:500] + "...")
                print("-----------------\n")
    else:
        print(f"Положите файл {test_file.name} рядом со скриптом для проверки.")