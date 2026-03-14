"""
Schedule Manager for lectures.
Refactored from schedule_manager.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from config.settings import SCHEDULE_FILE, LINKS_FILE
from utils.json_ops import read_json, write_json
from utils.console import (
    print_header, print_section, print_success, print_error,
    print_warning, print_info, print_menu_item, get_input, confirm
)

logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    Класс для управления расписанием лекций.
    """
    
    DAYS_OF_WEEK = [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]
    
    DAYS_RU = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье"
    }
    
    LECTURE_DISPLAY_NAMES = {
        "OperatingSystems": "Операционные системы",
        "IOT": "Интернет вещей",
        "ParallelProgramming": "Параллельное программирование"
    }
    
    def __init__(
        self,
        schedule_path: Path = SCHEDULE_FILE,
        links_path: Path = LINKS_FILE
    ):
        """
        Инициализация менеджера расписания.
        
        Args:
            schedule_path: Путь к файлу расписания
            links_path: Путь к файлу со ссылками
        """
        self.schedule_path = schedule_path
        self.links_path = links_path
        self.schedule = self._load_schedule()
        self.links = self._load_links()
    
    def _load_schedule(self) -> List[Dict]:
        """Загрузка расписания из JSON файла."""
        try:
            if self.schedule_path.exists():
                data = read_json(self.schedule_path)
                return data.get("schedule", [])
            return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке расписания: {e}")
            return []
    
    def _load_links(self) -> Dict[str, str]:
        """Загрузка ссылок на лекции."""
        try:
            return read_json(self.links_path)
        except Exception as e:
            logger.error(f"Ошибка при загрузке ссылок: {e}")
            return {}
    
    def _save_schedule(self) -> bool:
        """Сохранение расписания в JSON файл."""
        return write_json(self.schedule_path, {"schedule": self.schedule})
    
    def _validate_time(self, time_str: str) -> bool:
        """Проверка формата времени (HH:MM)."""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def _validate_day(self, day: str) -> bool:
        """Проверка корректности дня недели."""
        return day.lower() in self.DAYS_OF_WEEK
    
    def _get_lecture_display_name(self, lecture_key: str) -> str:
        """Получение отображаемого имени лекции."""
        return self.LECTURE_DISPLAY_NAMES.get(lecture_key, lecture_key)
    
    def display_schedule(self) -> None:
        """Отображение текущего расписания."""
        print_header("ТЕКУЩЕЕ РАСПИСАНИЕ ЛЕКЦИЙ")
        
        if not self.schedule:
            print_info("Расписание пусто.")
            return
        
        sorted_schedule = sorted(
            self.schedule,
            key=lambda x: (self.DAYS_OF_WEEK.index(x["day"]), x["time"])
        )
        
        current_day = None
        for item in sorted_schedule:
            day = item["day"]
            if day != current_day:
                current_day = day
                print_section(self.DAYS_RU.get(day, day))
            
            lecture_name = self._get_lecture_display_name(item["lecture"])
            print(f"  {item['time']} - {lecture_name} ({item['lecture']})")
    
    def display_available_lectures(self) -> None:
        """Отображение доступных лекций из links.json."""
        print_header("ДОСТУПНЫЕ ЛЕКЦИИ")
        
        if not self.links:
            print_info("Список лекций пуст.")
            return
        
        for key, url in self.links.items():
            display_name = self._get_lecture_display_name(key)
            print(f"  • {key} - {display_name}")
            print(f"    URL: {url}")
    
    def add_lecture(self) -> None:
        """Добавление лекции в расписание."""
        print_section("ДОБАВЛЕНИЕ ЛЕКЦИИ В РАСПИСАНИЕ")
        
        self.display_available_lectures()
        
        if not self.links:
            print_warning("Нет доступных лекций в links.json")
            return
        
        lecture = get_input("Введите название лекции (ключ из links.json)")
        
        if lecture not in self.links:
            print_error(f"Лекция '{lecture}' не найдена в links.json")
            return
        
        # Выбор дня
        print("\nДни недели:")
        for i, day in enumerate(self.DAYS_OF_WEEK, 1):
            print_menu_item(i, f"{self.DAYS_RU[day]} ({day})")
        
        day_input = get_input("\nВведите день недели (номер или название)").lower()
        
        if day_input.isdigit():
            day_idx = int(day_input) - 1
            if 0 <= day_idx < len(self.DAYS_OF_WEEK):
                day = self.DAYS_OF_WEEK[day_idx]
            else:
                print_error("Неверный номер дня")
                return
        elif day_input in self.DAYS_OF_WEEK:
            day = day_input
        else:
            print_error("Неверный день недели")
            return
        
        # Ввод времени
        time_input = get_input("Введите время (формат HH:MM, например 09:00)")
        
        if not self._validate_time(time_input):
            print_error("Неверный формат времени. Используйте HH:MM")
            return
        
        # Проверка конфликта
        for item in self.schedule:
            if item["day"] == day and item["time"] == time_input:
                print_warning(f"Конфликт: в это время уже запланирована лекция '{item['lecture']}'")
                if confirm("Перезаписать?"):
                    self.schedule.remove(item)
                    break
                else:
                    return
        
        # Добавление
        self.schedule.append({
            "day": day,
            "time": time_input,
            "lecture": lecture
        })
        
        if self._save_schedule():
            print_success(f"Лекция '{lecture}' добавлена на {self.DAYS_RU[day]} в {time_input}")
        else:
            print_error("Ошибка при сохранении")
    
    def remove_lecture(self) -> None:
        """Удаление лекции из расписания."""
        print_section("УДАЛЕНИЕ ЛЕКЦИИ ИЗ РАСПИСАНИЯ")
        
        if not self.schedule:
            print_info("Расписание пусто.")
            return
        
        print("\nТекущее расписание:")
        for i, item in enumerate(self.schedule, 1):
            day_ru = self.DAYS_RU.get(item["day"], item["day"])
            lecture_name = self._get_lecture_display_name(item["lecture"])
            print_menu_item(i, f"{day_ru} {item['time']} - {lecture_name}")
        
        try:
            choice = int(get_input("\nВведите номер лекции для удаления"))
            if 1 <= choice <= len(self.schedule):
                removed = self.schedule.pop(choice - 1)
                if self._save_schedule():
                    print_success(f"Лекция '{removed['lecture']}' удалена")
                else:
                    print_error("Ошибка при сохранении")
            else:
                print_error("Неверный номер")
        except ValueError:
            print_error("Введите число")
    
    def edit_lecture(self) -> None:
        """Редактирование времени лекции."""
        print_section("ПЕРЕНАЗНАЧЕНИЕ ВРЕМЕНИ ЛЕКЦИИ")
        
        if not self.schedule:
            print_info("Расписание пусто.")
            return
        
        print("\nТекущее расписание:")
        for i, item in enumerate(self.schedule, 1):
            day_ru = self.DAYS_RU.get(item["day"], item["day"])
            lecture_name = self._get_lecture_display_name(item["lecture"])
            print_menu_item(i, f"{day_ru} {item['time']} - {lecture_name}")
        
        try:
            choice = int(get_input("\nВведите номер лекции для редактирования"))
            if not (1 <= choice <= len(self.schedule)):
                print_error("Неверный номер")
                return
        except ValueError:
            print_error("Введите число")
            return
        
        item = self.schedule[choice - 1]
        print(f"\nРедактирование: {item['lecture']} ({self.DAYS_RU[item['day']]} {item['time']})")
        
        # Новый день
        print("\nДни недели:")
        for i, day in enumerate(self.DAYS_OF_WEEK, 1):
            print_menu_item(i, f"{self.DAYS_RU[day]} ({day})")
        
        day_input = get_input(f"\nНовый день (Enter чтобы оставить {item['day']})", item['day']).lower()
        
        if day_input.isdigit():
            day_idx = int(day_input) - 1
            if 0 <= day_idx < len(self.DAYS_OF_WEEK):
                new_day = self.DAYS_OF_WEEK[day_idx]
            else:
                print_error("Неверный номер дня")
                return
        elif day_input in self.DAYS_OF_WEEK:
            new_day = day_input
        else:
            print_error("Неверный день недели")
            return
        
        # Новое время
        time_input = get_input(f"Новое время (Enter чтобы оставить {item['time']})", item['time'])
        
        if not self._validate_time(time_input):
            print_error("Неверный формат времени")
            return
        
        # Проверка конфликта
        for other in self.schedule:
            if other != item and other["day"] == new_day and other["time"] == time_input:
                print_error(f"Конфликт: в это время уже запланирована лекция '{other['lecture']}'")
                return
        
        # Обновление
        item["day"] = new_day
        item["time"] = time_input
        
        if self._save_schedule():
            print_success(f"Лекция обновлена: {self.DAYS_RU[new_day]} {time_input}")
        else:
            print_error("Ошибка при сохранении")
    
    def get_next_lecture(self) -> Optional[Dict]:
        """
        Получение следующей лекции по расписанию.
        
        Returns:
            Словарь с информацией о лекции или None
        """
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")
        
        # Ищем лекции на сегодня после текущего времени
        today_lectures = [
            item for item in self.schedule
            if item["day"] == current_day and item["time"] > current_time
        ]
        
        if today_lectures:
            return min(today_lectures, key=lambda x: x["time"])
        
        # Если сегодня нет, ищем ближайший день
        day_order = self.DAYS_OF_WEEK
        current_idx = day_order.index(current_day)
        
        for offset in range(1, 8):
            next_idx = (current_idx + offset) % 7
            next_day = day_order[next_idx]
            
            next_day_lectures = [
                item for item in self.schedule
                if item["day"] == next_day
            ]
            
            if next_day_lectures:
                return min(next_day_lectures, key=lambda x: x["time"])
        
        return None
    
    def run_interactive(self) -> None:
        """Запуск интерактивного меню."""
        print_header("МЕНЕДЖЕР РАСПИСАНИЯ ЛЕКЦИЙ")
        
        while True:
            print("\nВыберите действие:")
            print_menu_item(1, "Показать расписание")
            print_menu_item(2, "Показать доступные лекции")
            print_menu_item(3, "Добавить лекцию")
            print_menu_item(4, "Удалить лекцию")
            print_menu_item(5, "Изменить время лекции")
            print_menu_item(0, "Выход")
            
            choice = get_input("\nВаш выбор")
            
            if choice == "1":
                self.display_schedule()
            elif choice == "2":
                self.display_available_lectures()
            elif choice == "3":
                self.add_lecture()
            elif choice == "4":
                self.remove_lecture()
            elif choice == "5":
                self.edit_lecture()
            elif choice == "0":
                print_info("До свидания!")
                break
            else:
                print_error("Неверный выбор")
