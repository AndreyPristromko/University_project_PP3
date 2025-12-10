from datetime import datetime, date, time
from typing import Optional
from config.constants import SlotStatus, DATE_FORMAT, TIME_FORMAT, DATETIME_FORMAT


class TimeSlot:
    def __init__(
        self,
        slot_date: date,
        start_time: time,
        end_time: time,
        status: SlotStatus = SlotStatus.FREE,
        expert_id: Optional[int] = None,
        expert_name: Optional[str] = None
    ):
        self.slot_date = slot_date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.expert_id = expert_id
        self.expert_name = expert_name
    
    def is_free(self) -> bool:
        return self.status == SlotStatus.FREE
    
    def is_booked(self) -> bool:
        return self.status in (SlotStatus.BOOKED, SlotStatus.CONFIRMED)
    
    def is_pending(self) -> bool:
        return self.status == SlotStatus.PENDING
    
    def book(self, expert_id: int, expert_name: str) -> bool:
        if not self.is_free():
            return False
        
        self.expert_id = expert_id
        self.expert_name = expert_name
        self.status = SlotStatus.PENDING
        return True
    
    def confirm(self) -> bool:
        if self.status != SlotStatus.PENDING:
            return False
        
        self.status = SlotStatus.CONFIRMED
        return True
    
    def release(self) -> None:
        self.status = SlotStatus.FREE
        self.expert_id = None
        self.expert_name = None
    
    def get_datetime_start(self) -> datetime:
        return datetime.combine(self.slot_date, self.start_time)
    
    def get_datetime_end(self) -> datetime:
        return datetime.combine(self.slot_date, self.end_time)
    
    def get_duration_minutes(self) -> int:
        duration = self.get_datetime_end() - self.get_datetime_start()
        return int(duration.total_seconds() / 60)
    
    def get_weekday(self) -> int:
        return self.slot_date.weekday()
    
    def format_date(self) -> str:
        return self.slot_date.strftime(DATE_FORMAT)
    
    def format_time_range(self) -> str:
        start = self.start_time.strftime(TIME_FORMAT)
        end = self.end_time.strftime(TIME_FORMAT)
        return f"{start}-{end}"
    
    def format_full(self) -> str:
        return f"{self.format_date()} {self.format_time_range()}"
    
    def to_dict(self) -> dict:
        return {
            "date": self.slot_date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "formatted": self.format_full()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TimeSlot":
        slot_date = date.fromisoformat(data["date"])
        start_time = time.fromisoformat(data["start_time"])
        end_time = time.fromisoformat(data["end_time"])
        status = SlotStatus(data["status"])
        
        return cls(
            slot_date=slot_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
            expert_id=data.get("expert_id"),
            expert_name=data.get("expert_name")
        )
    
    def __str__(self) -> str:
        status_str = "🟢" if self.is_free() else "🔴"
        expert_info = f" ({self.expert_name})" if self.expert_name else ""
        return f"{status_str} {self.format_full()}{expert_info}"
    
    def __repr__(self) -> str:
        return (
            f"TimeSlot(date={self.slot_date}, "
            f"time={self.format_time_range()}, "
            f"status={self.status.value}, "
            f"expert={self.expert_name})"
        )
