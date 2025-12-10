from typing import List, Optional, Dict
from datetime import date, timedelta
from collections import defaultdict

from models.timeslot import TimeSlot
from models.expert import Expert
from config.constants import SlotStatus, Weekday
from utils.date_utils import get_today
from utils.logger import get_logger

logger = get_logger(__name__)


class Schedule:
    def __init__(self):
        self.slots: List[TimeSlot] = []
        self._index: Dict[date, List[TimeSlot]] = defaultdict(list)
    
    def add_slot(self, slot: TimeSlot) -> None:
        self.slots.append(slot)
        self._index[slot.slot_date].append(slot)
        logger.debug(f"Добавлен слот: {slot.format_full()}")
    
    def add_slots(self, slots: List[TimeSlot]) -> None:
        for slot in slots:
            self.add_slot(slot)
        logger.info(f"Добавлено {len(slots)} слотов в расписание")
    
    def remove_slot(self, slot: TimeSlot) -> bool:
        try:
            self.slots.remove(slot)
            self._index[slot.slot_date].remove(slot)
            logger.debug(f"Удалён слот: {slot.format_full()}")
            return True
        except ValueError:
            logger.warning(f"Слот не найден для удаления: {slot.format_full()}")
            return False
    
    def get_all_slots(self) -> List[TimeSlot]:
        return self.slots.copy()
    
    def get_free_slots(self) -> List[TimeSlot]:
        return [slot for slot in self.slots if slot.is_free()]
    
    def get_booked_slots(self) -> List[TimeSlot]:
        return [slot for slot in self.slots if slot.is_booked()]
    
    def get_pending_slots(self) -> List[TimeSlot]:
        return [slot for slot in self.slots if slot.is_pending()]
    
    def get_slots_by_date(self, target_date: date) -> List[TimeSlot]:
        return self._index.get(target_date, []).copy()
    
    def get_slots_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[TimeSlot]:
        result = []
        current_date = start_date
        
        while current_date <= end_date:
            result.extend(self._index.get(current_date, []))
            current_date += timedelta(days=1)
        
        return result
    
    def get_slots_by_weekday(self, weekday: Weekday) -> List[TimeSlot]:
        weekday_num = list(Weekday).index(weekday)
        return [slot for slot in self.slots if slot.get_weekday() == weekday_num]
    
    def get_slots_by_expert(self, expert_id: int) -> List[TimeSlot]:
        return [slot for slot in self.slots if slot.expert_id == expert_id]
    
    def find_slot(
        self,
        target_date: date,
        start_time_str: str
    ) -> Optional[TimeSlot]:
        slots_for_date = self.get_slots_by_date(target_date)
        
        for slot in slots_for_date:
            if slot.start_time.strftime("%H:%M") == start_time_str:
                return slot
        
        return None
    
    def book_slot(
        self,
        slot: TimeSlot,
        expert: Expert
    ) -> bool:
        if slot.book(expert.expert_id, expert.name):
            expert.add_pending_slot(slot.slot_date)
            logger.info(f"Слот {slot.format_full()} забронирован для {expert.name}")
            return True
        
        logger.warning(f"Не удалось забронировать слот {slot.format_full()}")
        return False
    
    def confirm_slot(self, slot: TimeSlot, expert: Expert) -> bool:
        if slot.confirm():
            expert.add_confirmed_slot(slot.slot_date)
            logger.info(f"Слот {slot.format_full()} подтверждён для {expert.name}")
            return True
        
        return False
    
    def release_slot(self, slot: TimeSlot, expert: Optional[Expert] = None) -> None:
        slot.release()
        
        if expert:
            expert.remove_slot(slot.slot_date)
        
        logger.info(f"Слот {slot.format_full()} освобождён")
    
    def get_statistics(self) -> Dict[str, int]:
        total = len(self.slots)
        free = len(self.get_free_slots())
        booked = len(self.get_booked_slots())
        pending = len(self.get_pending_slots())
        
        return {
            "total": total,
            "free": free,
            "booked": booked,
            "pending": pending,
            "confirmed": booked - pending,
            "utilization_percent": round((booked / total * 100) if total > 0 else 0, 2)
        }
    
    def get_dates_with_slots(self) -> List[date]:
        return sorted(self._index.keys())
    
    def get_unique_experts(self) -> List[Dict[str, any]]:
        experts_map = {}
        
        for slot in self.slots:
            if slot.expert_id and slot.expert_id not in experts_map:
                experts_map[slot.expert_id] = {
                    "expert_id": slot.expert_id,
                    "name": slot.expert_name,
                    "slots_count": 0
                }
            
            if slot.expert_id:
                experts_map[slot.expert_id]["slots_count"] += 1
        
        return list(experts_map.values())
    
    def clear(self) -> None:
        self.slots.clear()
        self._index.clear()
        logger.info("Расписание очищено")
    
    def filter_future_slots(self) -> List[TimeSlot]:
        today = get_today()
        return [slot for slot in self.slots if slot.slot_date >= today]
    
    def sort_by_date(self) -> None:
        self.slots.sort(key=lambda s: (s.slot_date, s.start_time))
        logger.debug("Слоты отсортированы по дате и времени")
    
    def __len__(self) -> int:
        return len(self.slots)
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"Schedule(total={stats['total']}, "
            f"free={stats['free']}, "
            f"booked={stats['booked']})"
        )
    
    def __repr__(self) -> str:
        return f"Schedule(slots_count={len(self.slots)})"
