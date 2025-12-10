from datetime import date, time
from typing import List, Optional, Tuple
from config.constants import Weekday, WEEKDAYS_SHORT, WORK_START_TIME, WORK_END_TIME
from utils.date_utils import parse_date, parse_time, parse_time_range


class Validator:
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[date], str]:
        parsed_date = parse_date(date_str)
        
        if parsed_date is None:
            return False, None, "Некорректный формат даты. Используйте формат ДД.ММ.ГГГГ"
        if parsed_date < date.today():
            return False, None, "Дата не может быть в прошлом"
        
        return True, parsed_date, ""
    
    @staticmethod
    def validate_time(time_str: str) -> Tuple[bool, Optional[time], str]:
        parsed_time = parse_time(time_str)
        
        if parsed_time is None:
            return False, None, "Некорректный формат времени. Используйте формат ЧЧ:ММ"
        
        return True, parsed_time, ""
    
    @staticmethod
    def validate_time_range(time_range_str: str) -> Tuple[bool, Optional[Tuple[time, time]], str]:
        time_range = parse_time_range(time_range_str)
        
        if time_range is None:
            return False, None, "Некорректный формат временного диапазона. Используйте формат ЧЧ:ММ-ЧЧ:ММ"
        
        start_time, end_time = time_range
        
        if end_time <= start_time:
            return False, None, "Время окончания должно быть позже времени начала"
        
        return True, time_range, ""
    
    @staticmethod
    def validate_weekdays(text: str) -> Tuple[bool, List[Weekday], str]:
        if not text or not text.strip():
            return False, [], "Необходимо указать хотя бы один день недели"
        
        weekdays = []
        text_upper = text.upper().replace(",", " ").replace("  ", " ")
        parts = text_upper.split()
        
        for part in parts:
            part = part.strip()
            
            if part in WEEKDAYS_SHORT:
                weekdays.append(WEEKDAYS_SHORT[part])
                continue
            
            found = False
            for weekday in Weekday:
                if weekday.value.upper() == part:
                    weekdays.append(weekday)
                    found = True
                    break
            
            if not found and len(part) > 1:
                return False, [], f"Неизвестный день недели: {part}"
        
        if not weekdays:
            return False, [], "Не удалось распознать дни недели. Используйте формат: ПН, ВТ, СР или полные названия"
        
        weekdays = list(dict.fromkeys(weekdays))
        
        return True, weekdays, ""
    
    @staticmethod
    def validate_yes_no(text: str) -> Tuple[bool, Optional[bool], str]:
        if not text:
            return False, None, "Пустой ответ"
        
        text_lower = text.lower().strip()
        
        yes_options = ["да", "yes", "д", "y", "ок", "ok", "подтверждаю", "согласен"]
        no_options = ["нет", "no", "н", "n", "отмена", "не согласен"]
        
        if text_lower in yes_options:
            return True, True, ""
        
        if text_lower in no_options:
            return True, False, ""
        
        return False, None, "Пожалуйста, ответьте 'да' или 'нет'"
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Имя не может быть пустым"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, "Имя слишком короткое (минимум 2 символа)"
        
        if len(name) > 100:
            return False, "Имя слишком длинное (максимум 100 символов)"
        
        return True, ""
    
    @staticmethod
    def validate_working_hours(start_time: time, end_time: time) -> Tuple[bool, str]:
        work_start = parse_time(WORK_START_TIME)
        work_end = parse_time(WORK_END_TIME)
        
        if work_start is None or work_end is None:
            return True, ""
        
        if start_time < work_start:
            return False, f"Время начала раньше начала рабочего дня ({WORK_START_TIME})"
        
        if end_time > work_end:
            return False, f"Время окончания позже окончания рабочего дня ({WORK_END_TIME})"
        
        return True, ""
    
    @staticmethod
    def validate_slot_number(text: str, max_slots: int) -> Tuple[bool, Optional[int], str]:
        try:
            slot_num = int(text.strip())
            
            if slot_num < 1 or slot_num > max_slots:
                return False, None, f"Номер должен быть от 1 до {max_slots}"
            
            return True, slot_num, ""
        except ValueError:
            return False, None, "Введите корректный номер"
    
    @staticmethod
    def validate_slot_numbers(text: str, max_slots: int) -> Tuple[bool, List[int], str]:
        if not text or not text.strip():
            return False, [], "Необходимо указать хотя бы один номер"
        
        parts = text.replace(",", " ").split()
        numbers = []
        
        for part in parts:
            valid, num, error = Validator.validate_slot_number(part, max_slots)
            if not valid:
                return False, [], error
            if num:
                numbers.append(num)
        
        if not numbers:
            return False, [], "Не удалось распознать номера слотов"
        numbers = sorted(list(set(numbers)))
        
        return True, numbers, ""
