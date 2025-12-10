import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в файле .env")
    
    SCHEDULE_FILE_PATH = os.getenv(
        "SCHEDULE_FILE_PATH",
        str(DATA_DIR / "schedule.xlsx")
    )
    
    EXPERTS_FILE_PATH = str(DATA_DIR / "experts.json")
    
    DEFAULT_SESSION_DURATION = int(os.getenv("DEFAULT_SESSION_DURATION", "90"))
    WORK_START_TIME = os.getenv("WORK_START_TIME", "09:00")
    WORK_END_TIME = os.getenv("WORK_END_TIME", "21:00")
    
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FILE_PATH = str(LOGS_DIR / "bot.log")
    
    USER_RESPONSE_TIMEOUT = int(os.getenv("USER_RESPONSE_TIMEOUT", "3600"))
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    
    @classmethod
    def validate(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_schedule_file_path(cls) -> Path:
        return Path(cls.SCHEDULE_FILE_PATH)
    
    @classmethod
    def get_experts_file_path(cls) -> Path:
        return Path(cls.EXPERTS_FILE_PATH)

Settings.validate()
