from enum import Enum


class Weekday(Enum):
    MONDAY = "Понедельник"
    TUESDAY = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY = "Четверг"
    FRIDAY = "Пятница"
    SATURDAY = "Суббота"
    SUNDAY = "Воскресенье"


WEEKDAYS_SHORT = {
    "ПН": Weekday.MONDAY,
    "ВТ": Weekday.TUESDAY,
    "СР": Weekday.WEDNESDAY,
    "ЧТ": Weekday.THURSDAY,
    "ПТ": Weekday.FRIDAY,
    "СБ": Weekday.SATURDAY,
    "ВС": Weekday.SUNDAY,
}


class BotState(Enum):
    START = "start"
    ASKING_NAME = "asking_name"
    ASKING_DAYS = "asking_days"
    CONFIRMING_DAYS = "confirming_days"
    SHOWING_DRAFT = "showing_draft"
    CONFIRMING_SCHEDULE = "confirming_schedule"
    ADJUSTING_SLOTS = "adjusting_slots"
    EDITING_SCHEDULE = "editing_schedule"
    SELECTING_DATE = "selecting_date"
    SELECTING_TIME = "selecting_time"
    COMPLETED = "completed"                  


DEFAULT_SESSION_DURATION = 90
BREAK_DURATION = 15
WORK_START_TIME = "09:00"
WORK_END_TIME = "21:00"

TIME_SLOTS = [
    "09:00-10:30",
    "10:45-12:15",
    "12:30-14:00",
    "14:15-15:45",
    "16:00-17:30",
    "17:45-19:15",
    "19:30-21:00",
]


class SlotStatus(Enum):
    FREE = "free"
    BOOKED = "booked"
    PENDING = "pending"
    CONFIRMED = "confirmed"


BOT_COMMANDS = {
    "start": "Начать работу с ботом",
    "help": "Получить справку",
    "cancel": "Отменить текущую операцию",
    "schedule": "Посмотреть текущее расписание",
}


DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"  


MAX_SESSIONS_PER_DAY = 6
MIN_SESSIONS_REQUIRED = 1
MAX_WEEKS_AHEAD = 12
