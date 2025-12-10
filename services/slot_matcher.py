from typing import List, Optional, Dict
from datetime import date, timedelta
from collections import defaultdict

from models.timeslot import TimeSlot
from models.expert import Expert
from config.constants import Weekday, MAX_WEEKS_AHEAD, MIN_SESSIONS_REQUIRED
from utils.date_utils import get_dates_for_weekdays, get_today
from utils.logger import get_logger

logger = get_logger(__name__)


class SlotMatcher:
    def __init__(self, available_slots: List[TimeSlot]):
        self.available_slots = available_slots
        self._index_slots_by_date()
    
    def _index_slots_by_date(self) -> None:
        self.slots_by_date: Dict[date, List[TimeSlot]] = defaultdict(list)
        
        for slot in self.available_slots:
            self.slots_by_date[slot.slot_date].append(slot)
    
    def find_slots_for_expert(
        self,
        expert: Expert,
        sessions_count: int,
        weeks_ahead: int = MAX_WEEKS_AHEAD,
        start_date: Optional[date] = None
    ) -> List[TimeSlot]:
        if not expert.preferred_weekdays:
            logger.warning(f"У эксперта {expert.name} не указаны предпочтительные дни")
            return []
        
        if start_date is None:
            start_date = get_today()
        
        suitable_dates = get_dates_for_weekdays(
            start_date=start_date,
            weekdays=expert.preferred_weekdays,
            weeks=weeks_ahead
        )
        
        available_dates = [
            d for d in suitable_dates if not expert.is_date_booked(d)
        ]
        
        logger.info(
            f"Найдено {len(available_dates)} подходящих дат для {expert.name} "
            f"из {len(suitable_dates)} возможных"
        )
        
        selected_slots = self._select_slots_from_dates(
            dates=available_dates,
            count=sessions_count
        )
        
        logger.info(f"Подобрано {len(selected_slots)} слотов для {expert.name}")
        return selected_slots
    
    def _select_slots_from_dates(
        self,
        dates: List[date],
        count: int
    ) -> List[TimeSlot]:
        selected = []
        
        for target_date in dates:
            if len(selected) >= count:
                break
            
            free_slots = self._get_free_slots_for_date(target_date)
            
            if free_slots:
                selected.append(free_slots[0])
        
        return selected[:count]
    
    def _get_free_slots_for_date(self, target_date: date) -> List[TimeSlot]:
        slots_for_date = self.slots_by_date.get(target_date, [])
        return [slot for slot in slots_for_date if slot.is_free()]
    
    def find_slots_with_preferences(
        self,
        expert: Expert,
        sessions_count: int,
        preferred_time_ranges: Optional[List[str]] = None,
        weeks_ahead: int = MAX_WEEKS_AHEAD
    ) -> List[TimeSlot]:
        all_suitable_slots = self.find_slots_for_expert(
            expert=expert,
            sessions_count=sessions_count * 2, 
            weeks_ahead=weeks_ahead
        )
        
        if not preferred_time_ranges:
            return all_suitable_slots[:sessions_count]
        
        preferred_slots = []
        other_slots = []
        
        for slot in all_suitable_slots:
            time_range = slot.format_time_range()
            if time_range in preferred_time_ranges:
                preferred_slots.append(slot)
            else:
                other_slots.append(slot)
        
        result = preferred_slots + other_slots
        return result[:sessions_count]
    
    def distribute_evenly(
        self,
        expert: Expert,
        sessions_count: int,
        weeks_ahead: int = MAX_WEEKS_AHEAD
    ) -> List[TimeSlot]:
        if not expert.preferred_weekdays:
            return []
        
        start_date = get_today()
        selected_slots = []
        
        days_interval = max(7, (weeks_ahead * 7) // sessions_count)
        
        current_date = start_date
        attempts = 0
        max_attempts = weeks_ahead * 7
        
        while len(selected_slots) < sessions_count and attempts < max_attempts:
            attempts += 1
            
            weekday = list(Weekday)[current_date.weekday()]
            
            if weekday in expert.preferred_weekdays and not expert.is_date_booked(current_date):
                free_slots = self._get_free_slots_for_date(current_date)
                
                if free_slots:
                    selected_slots.append(free_slots[0])
                    current_date += timedelta(days=days_interval)
                else:
                    current_date += timedelta(days=1)
            else:
                current_date += timedelta(days=1)
        
        logger.info(f"Равномерно распределено {len(selected_slots)} слотов для {expert.name}")
        return selected_slots
    
    def find_alternative_slots(
        self,
        original_slot: TimeSlot,
        expert: Expert,
        alternatives_count: int = 3
    ) -> List[TimeSlot]:
        original_weekday = list(Weekday)[original_slot.slot_date.weekday()]
        
        suitable_dates = get_dates_for_weekdays(
            start_date=original_slot.slot_date + timedelta(days=7),
            weekdays=[original_weekday],
            weeks=4
        )
        
        alternatives = []
        for target_date in suitable_dates:
            if len(alternatives) >= alternatives_count:
                break
            
            if expert.is_date_booked(target_date):
                continue
            
            free_slots = self._get_free_slots_for_date(target_date)
            
            same_time_slots = [
                s for s in free_slots
                if s.start_time == original_slot.start_time
            ]
            
            if same_time_slots:
                alternatives.append(same_time_slots[0])
            elif free_slots:
                alternatives.append(free_slots[0])
        
        logger.info(f"Найдено {len(alternatives)} альтернатив для слота {original_slot.format_full()}")
        return alternatives
    
    def get_slot_statistics(self) -> Dict[str, int]:
        total = len(self.available_slots)
        free = sum(1 for s in self.available_slots if s.is_free())
        booked = sum(1 for s in self.available_slots if s.is_booked())
        pending = sum(1 for s in self.available_slots if s.is_pending())
        
        return {
            "total": total,
            "free": free,
            "booked": booked,
            "pending": pending,
            "utilization_percent": round((booked / total * 100) if total > 0 else 0, 2)
        }
    
    def check_conflicts(self, slots: List[TimeSlot]) -> List[str]:
        conflicts = []
        
        dates = [s.slot_date for s in slots]
        if len(dates) != len(set(dates)):
            conflicts.append("Обнаружены занятия в одну и ту же дату")
        
        sorted_slots = sorted(slots, key=lambda s: s.slot_date)
        for i in range(len(sorted_slots) - 1):
            diff = (sorted_slots[i + 1].slot_date - sorted_slots[i].slot_date).days
            if diff < 2:
                conflicts.append(
                    f"Слоты {sorted_slots[i].format_date()} и "
                    f"{sorted_slots[i + 1].format_date()} слишком близко"
                )
        
        return conflicts
