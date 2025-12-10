from typing import List, Optional, Dict
from datetime import date

from models.schedule import Schedule
from models.timeslot import TimeSlot
from models.expert import Expert
from services.schedule_parser import ScheduleParser
from services.slot_matcher import SlotMatcher
from config.settings import Settings
from config.constants import MAX_WEEKS_AHEAD, TIME_SLOTS
from utils.date_utils import (
    get_today, 
    get_dates_for_weekdays, 
    create_timeslots_for_dates,
    get_next_monday
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ScheduleController:
    def __init__(self):
        self.schedule = Schedule()
        self.parser = ScheduleParser(Settings.SCHEDULE_FILE_PATH)
        self.matcher: Optional[SlotMatcher] = None
    
    def initialize(self) -> bool:
        try:
            logger.info("Инициализация контроллера расписания")
            
            if not self.parser.load():
                logger.warning("Не удалось загрузить расписание, создаём новое")
                return self._generate_initial_schedule()
            
            slots = self.parser.read_all_slots()
            
            if not slots:
                logger.info("Расписание пустое, генерируем начальные слоты")
                return self._generate_initial_schedule()
            
            self.schedule.add_slots(slots)
            
            self.matcher = SlotMatcher(self.schedule.get_all_slots())
            
            logger.info(f"Расписание загружено: {len(slots)} слотов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            return False
    
    def _generate_initial_schedule(self) -> bool:
        try:
            logger.info("Генерация начального расписания")
            
            start_date = get_next_monday()
            
            from config.constants import Weekday
            weekdays = [
                Weekday.MONDAY,
                Weekday.TUESDAY,
                Weekday.WEDNESDAY,
                Weekday.THURSDAY,
                Weekday.FRIDAY
            ]
            
            dates = get_dates_for_weekdays(
                start_date=start_date,
                weekdays=weekdays,
                weeks=MAX_WEEKS_AHEAD
            )
            
            slots = create_timeslots_for_dates(dates, TIME_SLOTS)
            
            self.schedule.add_slots(slots)
            
            if not self.parser.write_slots(slots, clear_existing=True):
                logger.error("Не удалось сохранить начальное расписание")
                return False
            
            if not self.parser.save():
                logger.error("Не удалось сохранить файл расписания")
                return False
            
            self.matcher = SlotMatcher(self.schedule.get_all_slots())
            
            logger.info(f"Создано {len(slots)} слотов на {MAX_WEEKS_AHEAD} недель")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка генерации расписания: {e}", exc_info=True)
            return False
    
    def find_slots_for_expert(
        self,
        expert: Expert,
        sessions_count: int,
        distribute_evenly: bool = True
    ) -> List[TimeSlot]:
        if not self.matcher:
            logger.error("SlotMatcher не инициализирован")
            return []
        
        try:
            logger.info(f"Подбор {sessions_count} слотов для {expert.name}")
            
            if distribute_evenly:
                slots = self.matcher.distribute_evenly(
                    expert=expert,
                    sessions_count=sessions_count
                )
            else:
                slots = self.matcher.find_slots_for_expert(
                    expert=expert,
                    sessions_count=sessions_count
                )
            
            logger.info(f"Найдено {len(slots)} слотов для {expert.name}")
            return slots
            
        except Exception as e:
            logger.error(f"Ошибка подбора слотов: {e}", exc_info=True)
            return []
    
    def book_slots_for_expert(
        self,
        slots: List[TimeSlot],
        expert: Expert
    ) -> bool:
        try:
            logger.info(f"Бронирование {len(slots)} слотов для {expert.name}")
            
            booked_count = 0
            for slot in slots:
                if self.schedule.book_slot(slot, expert):
                    booked_count += 1
            
            logger.info(f"Забронировано {booked_count} из {len(slots)} слотов")
            return booked_count == len(slots)
            
        except Exception as e:
            logger.error(f"Ошибка бронирования: {e}", exc_info=True)
            return False
    
    def confirm_slots_for_expert(
        self,
        slots: List[TimeSlot],
        expert: Expert
    ) -> bool:
        try:
            logger.info(f"Подтверждение {len(slots)} слотов для {expert.name}")
            
            confirmed_count = 0
            for slot in slots:
                if self.schedule.confirm_slot(slot, expert):
                    confirmed_count += 1
            
            logger.info(f"Подтверждено {confirmed_count} из {len(slots)} слотов")
            return confirmed_count == len(slots)
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения: {e}", exc_info=True)
            return False
    
    def find_alternatives(
        self,
        original_slot: TimeSlot,
        expert: Expert,
        count: int = 3
    ) -> List[TimeSlot]:
        if not self.matcher:
            logger.error("SlotMatcher не инициализирован")
            return []
        
        try:
            alternatives = self.matcher.find_alternative_slots(
                original_slot=original_slot,
                expert=expert,
                alternatives_count=count
            )
            
            logger.info(f"Найдено {len(alternatives)} альтернатив")
            return alternatives
            
        except Exception as e:
            logger.error(f"Ошибка поиска альтернатив: {e}", exc_info=True)
            return []
    
    def save_schedule(self) -> bool:
        try:
            logger.info("Сохранение расписания")
            
            all_slots = self.schedule.get_all_slots()
            
            if not self.parser.write_slots(all_slots, clear_existing=True):
                logger.error("Не удалось записать слоты")
                return False
            
            if not self.parser.save():
                logger.error("Не удалось сохранить файл")
                return False
            
            logger.info("Расписание успешно сохранено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}", exc_info=True)
            return False
    
    def get_schedule_statistics(self) -> Dict[str, int]:
        return self.schedule.get_statistics()
    
    def get_free_slots_count(self) -> int:
        return len(self.schedule.get_free_slots())
    
    def release_expert_slots(self, expert: Expert) -> bool:
        try:
            expert_slots = self.schedule.get_slots_by_expert(expert.expert_id)
            
            for slot in expert_slots:
                self.schedule.release_slot(slot, expert)
            
            logger.info(f"Освобождено {len(expert_slots)} слотов для {expert.name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка освобождения слотов: {e}", exc_info=True)
            return False
    
    def get_schedule(self) -> Schedule:
        return self.schedule
    
    def close(self) -> None:
        if self.parser:
            self.parser.close()
        logger.info("Контроллер расписания закрыт")
