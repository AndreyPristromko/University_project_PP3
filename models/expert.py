from typing import List, Optional, Set
from datetime import date
from config.constants import Weekday, WEEKDAYS_SHORT


class Expert:
    def __init__(
        self,
        expert_id: int,
        name: str,
        telegram_id: Optional[int] = None,
        preferred_weekdays: Optional[List[Weekday]] = None
    ):
        self.expert_id = expert_id
        self.name = name
        self.telegram_id = telegram_id
        self.preferred_weekdays: List[Weekday] = preferred_weekdays or []
        self.confirmed_slots: List[date] = [] 
        self.pending_slots: List[date] = []    
    
    def set_preferred_weekdays(self, weekdays: List[Weekday]) -> None:
        self.preferred_weekdays = weekdays
    
    def add_preferred_weekday(self, weekday: Weekday) -> None:
        if weekday not in self.preferred_weekdays:
            self.preferred_weekdays.append(weekday)
    
    def remove_preferred_weekday(self, weekday: Weekday) -> None:
        if weekday in self.preferred_weekdays:
            self.preferred_weekdays.remove(weekday)
    
    def has_preferred_weekday(self, weekday: Weekday) -> bool:
        return weekday in self.preferred_weekdays
    
    def get_preferred_weekday_names(self) -> List[str]:
        return [day.value for day in self.preferred_weekdays]
    
    def add_confirmed_slot(self, slot_date: date) -> None:
        if slot_date not in self.confirmed_slots:
            self.confirmed_slots.append(slot_date)
            if slot_date in self.pending_slots:
                self.pending_slots.remove(slot_date)
    
    def add_pending_slot(self, slot_date: date) -> None:
        if slot_date not in self.pending_slots and slot_date not in self.confirmed_slots:
            self.pending_slots.append(slot_date)
    
    def remove_slot(self, slot_date: date) -> None:
        if slot_date in self.confirmed_slots:
            self.confirmed_slots.remove(slot_date)
        if slot_date in self.pending_slots:
            self.pending_slots.remove(slot_date)
    
    def get_total_slots_count(self) -> int:
        return len(self.confirmed_slots) + len(self.pending_slots)
    
    def get_confirmed_slots_count(self) -> int:
        return len(self.confirmed_slots)
    
    def has_slots(self) -> bool:
        return self.get_total_slots_count() > 0
    
    def is_date_booked(self, check_date: date) -> bool:
        return check_date in self.confirmed_slots or check_date in self.pending_slots
    
    @staticmethod
    def parse_weekdays_from_text(text: str) -> List[Weekday]:
        weekdays = []
        parts = text.upper().replace(",", " ").split()
        
        for part in parts:
            part = part.strip()
            if part in WEEKDAYS_SHORT:
                weekdays.append(WEEKDAYS_SHORT[part])
        
        return weekdays
    
    def to_dict(self) -> dict:
        return {
            "expert_id": self.expert_id,
            "name": self.name,
            "telegram_id": self.telegram_id,
            "preferred_weekdays": [day.name for day in self.preferred_weekdays],
            "confirmed_slots": [d.isoformat() for d in self.confirmed_slots],
            "pending_slots": [d.isoformat() for d in self.pending_slots]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Expert":
        preferred_weekdays = [
            Weekday[day_name] for day_name in data.get("preferred_weekdays", [])
        ]
        
        expert = cls(
            expert_id=data["expert_id"],
            name=data["name"],
            telegram_id=data.get("telegram_id"),
            preferred_weekdays=preferred_weekdays
        )
        
        expert.confirmed_slots = [
            date.fromisoformat(d) for d in data.get("confirmed_slots", [])
        ]
        expert.pending_slots = [
            date.fromisoformat(d) for d in data.get("pending_slots", [])
        ]
        
        return expert
    
    def __str__(self) -> str:
        days = ", ".join(self.get_preferred_weekday_names()) if self.preferred_weekdays else "не указаны"
        return f"{self.name} (предпочтения: {days}, слотов: {self.get_total_slots_count()})"
    
    def __repr__(self) -> str:
        return f"Expert(id={self.expert_id}, name='{self.name}', slots={self.get_total_slots_count()})"
