from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Optional
from config.constants import (
    Weekday, DATE_FORMAT, TIME_FORMAT, DATETIME_FORMAT,
    TIME_SLOTS, DEFAULT_SESSION_DURATION
)
from models.timeslot import TimeSlot


def parse_date(date_str: str, format_str: str = DATE_FORMAT) -> Optional[date]:
    try:
        return datetime.strptime(date_str, format_str).date()
    except (ValueError, TypeError):
        return None


def parse_time(time_str: str, format_str: str = TIME_FORMAT) -> Optional[time]:
    try:
        return datetime.strptime(time_str, format_str).time()
    except (ValueError, TypeError):
        return None


def parse_time_range(time_range_str: str) -> Optional[Tuple[time, time]]:
    try:
        start_str, end_str = time_range_str.split("-")
        start_time = parse_time(start_str.strip())
        end_time = parse_time(end_str.strip())
        
        if start_time and end_time:
            return (start_time, end_time)
        return None
    except (ValueError, AttributeError):
        return None


def format_date(d: date, format_str: str = DATE_FORMAT) -> str:
    return d.strftime(format_str)


def format_time(t: time, format_str: str = TIME_FORMAT) -> str:
    return t.strftime(format_str)


def get_weekday_name(d: date) -> str:
    weekday_num = d.weekday()
    weekdays = list(Weekday)
    return weekdays[weekday_num].value


def generate_dates_for_weeks(start_date: date, weeks: int = 12) -> List[date]:
    dates = []
    total_days = weeks * 7
    
    for i in range(total_days):
        current_date = start_date + timedelta(days=i)
        dates.append(current_date)
    
    return dates


def filter_by_weekday(dates: List[date], weekdays: List[Weekday]) -> List[date]:
    weekday_nums = []
    for weekday in weekdays:
        weekday_nums.append(list(Weekday).index(weekday))
    
    filtered = [d for d in dates if d.weekday() in weekday_nums]
    return filtered


def get_dates_for_weekdays(
    start_date: date,
    weekdays: List[Weekday],
    weeks: int = 12
) -> List[date]:
    all_dates = generate_dates_for_weeks(start_date, weeks)
    return filter_by_weekday(all_dates, weekdays)


def is_date_in_weekdays(d: date, weekdays: List[Weekday]) -> bool:
    weekday_nums = [list(Weekday).index(wd) for wd in weekdays]
    return d.weekday() in weekday_nums


def create_timeslot_from_range(
    slot_date: date,
    time_range_str: str
) -> Optional[TimeSlot]:
    time_range = parse_time_range(time_range_str)
    if not time_range:
        return None
    
    start_time, end_time = time_range
    return TimeSlot(
        slot_date=slot_date,
        start_time=start_time,
        end_time=end_time
    )


def create_timeslots_for_date(
    slot_date: date,
    time_ranges: Optional[List[str]] = None
) -> List[TimeSlot]:
    if time_ranges is None:
        time_ranges = TIME_SLOTS
    
    slots = []
    for time_range_str in time_ranges:
        slot = create_timeslot_from_range(slot_date, time_range_str)
        if slot:
            slots.append(slot)
    
    return slots


def create_timeslots_for_dates(
    dates: List[date],
    time_ranges: Optional[List[str]] = None
) -> List[TimeSlot]:
    all_slots = []
    for slot_date in dates:
        slots = create_timeslots_for_date(slot_date, time_ranges)
        all_slots.extend(slots)
    
    return all_slots


def get_time_from_minutes(minutes: int) -> time:
    hours = minutes // 60
    mins = minutes % 60
    return time(hour=hours, minute=mins)


def add_minutes_to_time(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t)
    new_dt = dt + timedelta(minutes=minutes)
    return new_dt.time()


def calculate_duration(start: time, end: time) -> int:
    start_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    duration = end_dt - start_dt
    return int(duration.total_seconds() / 60)


def format_date_readable(d: date) -> str:
    weekday_name = get_weekday_name(d)
    date_str = format_date(d)
    return f"{weekday_name}, {date_str}"


def get_today() -> date:
    return date.today()


def get_next_monday(from_date: Optional[date] = None) -> date:
    if from_date is None:
        from_date = get_today()
    
    days_ahead = 0 - from_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    
    return from_date + timedelta(days=days_ahead)
