"""
BBB Lecture Recorder.
Refactored from lecture_recorder.py
"""

import re
import os
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import (
    BBB_USER_NAME,
    BBB_MIN_PARTICIPANTS,
    BBB_HISTORY_SIZE,
    BBB_CHECK_INTERVAL,
    RECORDINGS_DIR,
    FFMPEG_AUDIO_BITRATE,
    FFMPEG_AUDIO_CODEC
)

logger = logging.getLogger(__name__)


def get_stereo_mix_device_name() -> Optional[str]:
    """
    Ищет точное название 'Стерео микшер' или 'Stereo Mix' в системе через FFmpeg.
    
    Returns:
        Название устройства или None если не найдено
    """
    try:
        cmd = [
            'ffmpeg',
            '-list_devices',
            'true',
            '-f',
            'dshow',
            '-i',
            'dummy'
        ]
        
        proc = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = proc.stderr.decode('utf-8', errors='ignore')
        if "Стерео" not in output and "Stereo" not in output:
            output = proc.stderr.decode('cp1251', errors='ignore')

        for line in output.splitlines():
            if "Стерео микшер" in line or "Stereo Mix" in line:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    return match.group(1)
                    
    except FileNotFoundError:
        logger.error("FFmpeg не установлен или не добавлен в PATH!")
        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске аудио-устройства: {e}")
        
    return "Стерео микшер"


class SystemAudioRecorder:
    """Класс для записи системного аудио через FFmpeg."""
    
    def __init__(self, filename: Optional[str] = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lecture_{timestamp}.mp3"
        
        self.filepath = RECORDINGS_DIR / filename
        self.process = None
        self.device_name = get_stereo_mix_device_name()

    def start(self) -> bool:
        """
        Запуск FFmpeg в фоновом процессе.
        
        Returns:
            True если успешно запущен
        """
        if not self.device_name:
            logger.error("Запись невозможна: не найден FFmpeg или аудио-устройство.")
            return False
            
        logger.info(f"Выбрано устройство записи: {self.device_name}")
        logger.info(f"FFmpeg начал запись в файл: {self.filepath}")
        
        cmd = [
            'ffmpeg',
            '-y',
            '-f', 'dshow',
            '-i', f'audio={self.device_name}',
            '-acodec', FFMPEG_AUDIO_CODEC,
            '-b:a', FFMPEG_AUDIO_BITRATE,
            str(self.filepath)
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        return True

    def stop(self) -> Optional[Path]:
        """
        Остановка FFmpeg.
        
        Returns:
            Путь к записанному файлу или None
        """
        if self.process and self.process.poll() is None:
            logger.info("Останавливаем запись аудио...")
            try:
                self.process.communicate(input=b'q', timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            logger.info(f"Аудио сохранено: {self.filepath}")
            
        return self.filepath if self.filepath.exists() else None


class BBBRecorder:
    """
    Класс для записи лекций с BigBlueButton.
    """
    
    def __init__(
        self,
        url: str,
        user_name: str = BBB_USER_NAME,
        min_participants: int = BBB_MIN_PARTICIPANTS,
        history_size: int = BBB_HISTORY_SIZE,
        check_interval: int = BBB_CHECK_INTERVAL,
        filename: Optional[str] = None
    ):
        """
        Инициализация рекордера.
        
        Args:
            url: URL лекции BBB
            user_name: Имя пользователя для входа
            min_participants: Минимальное количество участников
            history_size: Размер истории участников
            check_interval: Интервал проверки (секунды)
            filename: Имя файла для записи
        """
        self.url = url
        self.user_name = user_name
        self.min_participants = min_participants
        self.history_size = history_size
        self.check_interval = check_interval
        self.driver = None
        
        self.audio_recorder = SystemAudioRecorder(filename)

    def start_session(self) -> Optional[Path]:
        """
        Запуск сессии записи.
        
        Returns:
            Путь к записанному файлу или None
        """
        chrome_options = Options()
        chrome_options.add_argument("--use-fake-ui-for-media-stream")

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.maximize_window()
        wait = WebDriverWait(self.driver, 30)

        recorded_file = None

        try:
            logger.info(f"Подключение к: {self.url}")
            self.driver.get(self.url)

            # Вход
            try:
                name_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[id$='join_name']"))
                )
                name_input.clear()
                name_input.send_keys(self.user_name)
                join_btn = wait.until(EC.element_to_be_clickable((By.ID, "room-join")))
                join_btn.click()
            except Exception:
                logger.warning("Вход пропущен (возможно, уже авторизованы).")

            # Подключение аудио
            logger.info("Ожидание кнопки 'Только слушать'...")
            try:
                listen_btn_xpath = "//button[@aria-label='Listen only' or @aria-label='Только слушать'] | //span[contains(text(), 'Listen only') or contains(text(), 'Только слушать')]"
                listen_only_btn = wait.until(EC.element_to_be_clickable((By.XPATH, listen_btn_xpath)))
                listen_only_btn.click()
                logger.info("Режим аудио выбран.")
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Не удалось нажать кнопку аудио: {e}")

            # Старт записи
            if not self.audio_recorder.start():
                logger.error("Прерываем сеанс: не удалось инициализировать FFmpeg.")
                return None

            # Мониторинг участников
            self._monitor_session()

        except Exception as e:
            logger.error(f"Критическая ошибка в браузере: {e}")
        
        finally:
            recorded_file = self.audio_recorder.stop()
            
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Браузер закрыт.")
                except:
                    pass
            
            return recorded_file

    def _monitor_session(self) -> Optional[Path]:
        """
        Мониторинг сессии и участников.
        
        Returns:
            Путь к файлу или None
        """
        participants_history = []
        warming_up = True
        warmup_counter = 0
        
        logger.info("Мониторинг запущен.")
        
        while True:
            if not self.driver.window_handles:
                logger.info("Браузер закрыт вручную.")
                break

            # Проверка завершения встречи
            end_msg = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Сеанс завершен') or contains(text(), 'Meeting ended')]"
            )
            if end_msg or "logout" in self.driver.current_url or "ended" in self.driver.current_url:
                logger.info("Обнаружено завершение встречи.")
                break

            try:
                user_container = self.driver.find_element(By.XPATH, "//*[@data-test='userList']")
                match = re.search(r'\((\d+)\)', user_container.text)
                
                if match:
                    current_people = int(match.group(1))
                    participants_history.append(current_people)
                    if len(participants_history) > self.history_size:
                        participants_history.pop(0)

                    peak = max(participants_history)
                    ratio = current_people / peak if peak > 0 else 1
                    
                    print(f"\rУчастников: {current_people} (Пик: {peak}) | Осталось: {int(ratio*100)}%", end="")

                    if warming_up:
                        warmup_counter += 1
                        if warmup_counter > 20:
                            warming_up = False
                    else:
                        if peak >= self.min_participants and ratio <= 0.35:
                            logger.info("65%+ аудитории вышло. Завершаем запись.")
                            break
            except Exception:
                pass

            time.sleep(self.check_interval)
        
        return None
