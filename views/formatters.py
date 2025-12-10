from typing import List, Dict
from models.timeslot import TimeSlot
from models.expert import Expert
from utils.date_utils import get_weekday_name, format_date_readable


class ScheduleFormatter:
    @staticmethod
    def format_slot(slot: TimeSlot, show_expert: bool = True, number: int = None) -> str:
        status_emoji = {
            "free": "🟢",
            "booked": "🔴",
            "pending": "🟡",
            "confirmed": "✅"
        }
        emoji = status_emoji.get(slot.status.value, "⚪")
        
        weekday = get_weekday_name(slot.slot_date)
        date_str = slot.format_date()
        time_str = slot.format_time_range()
        
        parts = []
        
        if number:
            parts.append(f"{number}.")
        
        parts.append(f"{emoji} {weekday}, {date_str}")
        parts.append(f"⏰ {time_str}")
        
        if show_expert and slot.expert_name:
            parts.append(f"👤 {slot.expert_name}")
        
        return " | ".join(parts)
    
    @staticmethod
    def format_slots_list(
        slots: List[TimeSlot],
        show_expert: bool = True,
        numbered: bool = True
    ) -> str:
        if not slots:
            return "📭 Нет слотов для отображения"
        
        lines = []
        for i, slot in enumerate(slots, start=1):
            number = i if numbered else None
            line = ScheduleFormatter.format_slot(slot, show_expert, number)
            lines.append(line)
        
        return "\n\n".join(lines)
    
    @staticmethod
    def format_schedule_draft(slots: List[TimeSlot]) -> str:
        if not slots:
            return "📭 Расписание пусто"
        
        sorted_slots = sorted(slots, key=lambda s: (s.slot_date, s.start_time))
        
        lines = ["📅 Ваше расписание:\n"]
        
        for i, slot in enumerate(sorted_slots, start=1):
            weekday = get_weekday_name(slot.slot_date)
            date_str = slot.format_date()
            time_str = slot.format_time_range()
            duration = slot.get_duration_minutes()
            
            line = f"{i}. {weekday}, {date_str}\n   ⏰ {time_str} ({duration} мин)"
            lines.append(line)
        
        return "\n\n".join(lines)
    
    @staticmethod
    def format_schedule_summary(slots: List[TimeSlot]) -> str:
        if not slots:
            return "Нет занятий"
        
        total = len(slots)
        weekdays_count = {}
        for slot in slots:
            weekday = get_weekday_name(slot.slot_date)
            weekdays_count[weekday] = weekdays_count.get(weekday, 0) + 1
        sorted_slots = sorted(slots, key=lambda s: s.slot_date)
        first_date = format_date_readable(sorted_slots[0].slot_date)
        last_date = format_date_readable(sorted_slots[-1].slot_date)
        
        lines = [
            f"📊 Сводка расписания:",
            f"",
            f"Всего занятий: {total}",
            f"Период: {first_date} — {last_date}",
            f"",
            f"Распределение по дням:"
        ]
        
        for weekday, count in sorted(weekdays_count.items()):
            lines.append(f"  • {weekday}: {count}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_expert_info(expert: Expert) -> str:
        days = ", ".join(expert.get_preferred_weekday_names())
        confirmed = expert.get_confirmed_slots_count()
        total = expert.get_total_slots_count()
        
        lines = [
            f"👤 Эксперт: {expert.name}",
            f"📅 Предпочтительные дни: {days}",
            f"✅ Подтверждённых занятий: {confirmed}",
            f"📋 Всего запланировано: {total}"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def format_alternatives(
        original_slot: TimeSlot,
        alternatives: List[TimeSlot]
    ) -> str:
        lines = [
            f"❌ Вместо: {ScheduleFormatter.format_slot(original_slot, show_expert=False)}",
            f"",
            f"🔄 Альтернативные варианты:"
        ]
        
        if not alternatives:
            lines.append("\n😕 Альтернатив не найдено")
        else:
            for i, alt_slot in enumerate(alternatives, start=1):
                line = ScheduleFormatter.format_slot(alt_slot, show_expert=False, number=i)
                lines.append(f"\n{line}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_statistics(stats: Dict[str, int]) -> str:
        total = stats.get("total", 0)
        free = stats.get("free", 0)
        booked = stats.get("booked", 0)
        pending = stats.get("pending", 0)
        utilization = stats.get("utilization_percent", 0)
        
        lines = [
            "📊 Статистика расписания:",
            "",
            f"Всего слотов: {total}",
            f"🟢 Свободно: {free}",
            f"🔴 Занято: {booked}",
            f"🟡 Ожидает подтверждения: {pending}",
            f"",
            f"Загруженность: {utilization}%"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def format_confirmation_request(slots: List[TimeSlot]) -> str:
        draft = ScheduleFormatter.format_schedule_draft(slots)
        summary = ScheduleFormatter.format_schedule_summary(slots)
        
        return f"{draft}\n\n{summary}"
    
    @staticmethod
    def format_date_range(start_date, end_date) -> str:
        start_str = format_date_readable(start_date)
        end_str = format_date_readable(end_date)
        
        return f"{start_str} — {end_str}"
    
    @staticmethod
    def format_weekdays_list(weekdays: List) -> str:
        return ", ".join([day.value for day in weekdays])
    
    @staticmethod
    def format_slot_compact(slot: TimeSlot) -> str:
        return f"{slot.format_date()} {slot.format_time_range()}"
    
    @staticmethod
    def format_error_message(error_text: str) -> str:
        return f"❌ Ошибка: {error_text}"
    
    @staticmethod
    def format_success_message(message: str) -> str:
        return f"✅ {message}"
