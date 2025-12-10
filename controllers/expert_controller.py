import json
from pathlib import Path
from typing import Optional, Dict, List

from models.expert import Expert
from config.constants import Weekday
from config.settings import Settings
from services.validator import Validator
from utils.logger import get_logger

logger = get_logger(__name__)


class ExpertController:
    def __init__(self):
        self.experts: Dict[int, Expert] = {}
        self.experts_file = Path(Settings.EXPERTS_FILE_PATH)
        self._next_expert_id = 1
    
    def initialize(self) -> bool:
        try:
            logger.info("Инициализация контроллера экспертов")
            
            if self.experts_file.exists():
                self._load_experts_from_file()
            else:
                logger.info("Файл экспертов не найден, начинаем с пустого списка")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            return False
    
    def _load_experts_from_file(self) -> None:
        try:
            with open(self.experts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for expert_data in data.get("experts", []):
                expert = Expert.from_dict(expert_data)
                if expert.telegram_id:
                    self.experts[expert.telegram_id] = expert
                
                if expert.expert_id >= self._next_expert_id:
                    self._next_expert_id = expert.expert_id + 1
            
            logger.info(f"Загружено {len(self.experts)} экспертов")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки экспертов: {e}", exc_info=True)
    
    def save_experts(self) -> bool:
        try:
            self.experts_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "experts": [expert.to_dict() for expert in self.experts.values()]
            }
            
            with open(self.experts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Сохранено {len(self.experts)} экспертов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения экспертов: {e}", exc_info=True)
            return False
    
    def get_or_create_expert(
        self,
        telegram_id: int,
        name: Optional[str] = None
    ) -> Expert:
        if telegram_id in self.experts:
            logger.debug(f"Эксперт найден: {self.experts[telegram_id].name}")
            return self.experts[telegram_id]
        
        expert = Expert(
            expert_id=self._next_expert_id,
            name=name or f"Эксперт {self._next_expert_id}",
            telegram_id=telegram_id
        )
        
        self._next_expert_id += 1
        self.experts[telegram_id] = expert
        
        logger.info(f"Создан новый эксперт: {expert.name} (ID: {expert.expert_id})")
        return expert
    
    def update_expert_name(self, telegram_id: int, name: str) -> bool:
        valid, error = Validator.validate_name(name)
        if not valid:
            logger.warning(f"Некорректное имя: {error}")
            return False
        
        expert = self.get_or_create_expert(telegram_id, name)
        expert.name = name.strip()
        
        logger.info(f"Имя эксперта обновлено: {expert.name}")
        return True
    
    def set_expert_preferences(
        self,
        telegram_id: int,
        weekdays_text: str
    ) -> tuple[bool, str, List[Weekday]]:
        valid, weekdays, error = Validator.validate_weekdays(weekdays_text)
        if not valid:
            logger.warning(f"Некорректные дни недели: {error}")
            return False, error, []
        
        expert = self.get_or_create_expert(telegram_id)
        expert.set_preferred_weekdays(weekdays)
        
        logger.info(f"Предпочтения установлены для {expert.name}: {weekdays}")
        return True, "", weekdays
    
    def get_expert(self, telegram_id: int) -> Optional[Expert]:
        return self.experts.get(telegram_id)
    
    def get_expert_by_id(self, expert_id: int) -> Optional[Expert]:
        for expert in self.experts.values():
            if expert.expert_id == expert_id:
                return expert
        return None
    
    def get_all_experts(self) -> List[Expert]:
        return list(self.experts.values())
    
    def has_expert(self, telegram_id: int) -> bool:
        return telegram_id in self.experts
    
    def add_pending_slots(
        self,
        telegram_id: int,
        slot_dates: List
    ) -> bool:
        expert = self.get_expert(telegram_id)
        if not expert:
            logger.warning(f"Эксперт не найден: {telegram_id}")
            return False
        
        for slot_date in slot_dates:
            expert.add_pending_slot(slot_date)
        
        logger.info(f"Добавлено {len(slot_dates)} ожидающих слотов для {expert.name}")
        return True
    
    def confirm_pending_slots(self, telegram_id: int) -> bool:
        expert = self.get_expert(telegram_id)
        if not expert:
            logger.warning(f"Эксперт не найден: {telegram_id}")
            return False
        
        for slot_date in expert.pending_slots.copy():
            expert.add_confirmed_slot(slot_date)
        
        logger.info(f"Подтверждены слоты для {expert.name}")
        return True
    
    def clear_pending_slots(self, telegram_id: int) -> bool:
        expert = self.get_expert(telegram_id)
        if not expert:
            logger.warning(f"Эксперт не найден: {telegram_id}")
            return False
        
        count = len(expert.pending_slots)
        expert.pending_slots.clear()
        
        logger.info(f"Очищено {count} ожидающих слотов для {expert.name}")
        return True
    
    def get_expert_statistics(self, telegram_id: int) -> Optional[Dict]:
        expert = self.get_expert(telegram_id)
        if not expert:
            return None
        
        return {
            "name": expert.name,
            "expert_id": expert.expert_id,
            "preferred_days": expert.get_preferred_weekday_names(),
            "confirmed_slots": expert.get_confirmed_slots_count(),
            "pending_slots": len(expert.pending_slots),
            "total_slots": expert.get_total_slots_count(),
            "has_preferences": len(expert.preferred_weekdays) > 0
        }
    
    def delete_expert(self, telegram_id: int) -> bool:
        if telegram_id in self.experts:
            expert_name = self.experts[telegram_id].name
            del self.experts[telegram_id]
            logger.info(f"Эксперт удалён: {expert_name}")
            return True
        
        logger.warning(f"Эксперт не найден для удаления: {telegram_id}")
        return False
    
    def get_experts_count(self) -> int:
        return len(self.experts)
