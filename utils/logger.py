import logging
import sys
from pathlib import Path
from typing import Optional
from config.settings import Settings


class Logger:
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "ScheduleBot") -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        
        return cls._instance
    
    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        
        log_level = getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        if logger.handlers:
            return logger
        
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        try:
            log_file_path = Path(Settings.LOG_FILE_PATH)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_file_path,
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Не удалось настроить логирование в файл: {e}")
        
        return logger

def get_logger(name: str = "ScheduleBot") -> logging.Logger:
    return Logger.get_logger(name)

def log_info(message: str, logger_name: str = "ScheduleBot") -> None:
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: str = "ScheduleBot") -> None:
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: str = "ScheduleBot", exc_info: bool = False) -> None:
    get_logger(logger_name).error(message, exc_info=exc_info)


def log_debug(message: str, logger_name: str = "ScheduleBot") -> None:
    get_logger(logger_name).debug(message)


def log_exception(message: str, logger_name: str = "ScheduleBot") -> None:
    get_logger(logger_name).exception(message)
