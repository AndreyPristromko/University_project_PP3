from typing import Dict, Optional, List, Tuple
from datetime import date

from controllers.schedule_controller import ScheduleController
from controllers.expert_controller import ExpertController
from models.expert import Expert
from models.timeslot import TimeSlot
from config.constants import BotState
from services.validator import Validator
from views.bot_messages import BotMessages
from views.formatters import ScheduleFormatter
from utils.logger import get_logger

logger = get_logger(__name__)


class BotController:
    def __init__(
        self,
        schedule_controller: ScheduleController,
        expert_controller: ExpertController
    ):
        self.schedule_ctrl = schedule_controller
        self.expert_ctrl = expert_controller
        
        self.user_states: Dict[int, BotState] = {}
        self.session_data: Dict[int, Dict] = {}
        
        logger.info("BotController инициализирован")
    
    def initialize(self) -> bool:
        try:
            logger.info("Инициализация BotController")
            
            if not self.schedule_ctrl.initialize():
                logger.error("Не удалось инициализировать ScheduleController")
                return False
            
            if not self.expert_ctrl.initialize():
                logger.error("Не удалось инициализировать ExpertController")
                return False
            
            logger.info("BotController успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации BotController: {e}", exc_info=True)
            return False
    
    def _get_state(self, user_id: int) -> BotState:
        return self.user_states.get(user_id, BotState.START)
    
    def _set_state(self, user_id: int, state: BotState) -> None:
        self.user_states[user_id] = state
        logger.debug(f"User {user_id} state: {state.value}")
    
    def _get_session_data(self, user_id: int) -> Dict:
        if user_id not in self.session_data:
            self.session_data[user_id] = {}
        return self.session_data[user_id]
    
    def _clear_session(self, user_id: int) -> None:
        if user_id in self.session_data:
            del self.session_data[user_id]
        if user_id in self.user_states:
            del self.user_states[user_id]
        logger.debug(f"Session cleared for user {user_id}")

    
    def handle_start(self, user_id: int) -> str:
        logger.info(f"User {user_id} opened main menu")
        
        return BotMessages.WELCOME
    
    def handle_new_schedule(self, user_id: int) -> str:
        logger.info(f"User {user_id} started creating new schedule")
        
        self._clear_session(user_id)
        
        self._set_state(user_id, BotState.ASKING_NAME)
        
        return BotMessages.START + "\n\n" + BotMessages.ASK_NAME
    
    def handle_help(self, user_id: int) -> str:
        return BotMessages.HELP
    
    def handle_cancel(self, user_id: int) -> str:
        self._clear_session(user_id)
        return BotMessages.CANCELLED
    
    def handle_edit_schedule(self, user_id: int) -> str:
        logger.info(f"User {user_id} requested schedule editing")
        
        expert = self.expert_ctrl.get_expert(user_id)
        
        if not expert:
            return """
❌ У вас ещё нет сохранённого расписания.

Сначала создайте новое расписание, нажав кнопку "📅 Создать новое расписание"
            """
        
        if not expert.confirmed_slots:
            return f"""
📋 Эксперт: {expert.name}

❌ У вас нет подтверждённых слотов в расписании.

Создайте новое расписание, нажав кнопку "📅 Создать новое расписание"
            """
        
        self._set_state(user_id, BotState.EDITING_SCHEDULE)
        
        all_slots = self.schedule_ctrl.schedule.get_all_slots()
        
        confirmed_slot_objects = [
            slot for slot in all_slots
            if slot.expert_id == user_id and slot.status.value in ['confirmed', 'pending']
        ]
        
        if not confirmed_slot_objects:
            return """
❌ Не удалось найти ваши слоты в расписании.

Попробуйте создать новое расписание.
            """
        
        from views.formatters import ScheduleFormatter
        
        slots_info = ScheduleFormatter.format_slots_list(confirmed_slot_objects)
        
        return f"""
📋 Ваше текущее расписание:

Эксперт: {expert.name}
Предпочитаемые дни: {', '.join(expert.get_preferred_weekday_names())}

{slots_info}

Всего занятий: {len(confirmed_slot_objects)}

Выберите действие из кнопок ниже:
        """
    
    def handle_add_lesson(self, user_id: int) -> str:
        logger.info(f"User {user_id} wants to add lesson")
        
        expert = self.expert_ctrl.get_expert(user_id)
        if not expert:
            return "❌ Ошибка: эксперт не найден"
        
        self._set_state(user_id, BotState.SELECTING_DATE)
        
        return """
📅 Выберите дату для нового занятия:

Нажмите на одну из кнопок ниже или напишите дату в формате ДД.ММ.ГГГГ (например: 15.12.2025)
        """
    
    def handle_delete_lessons(self, user_id: int) -> str:
        logger.info(f"User {user_id} wants to delete lessons")
        
        self._set_state(user_id, BotState.EDITING_SCHEDULE)
        
        return """
🗑️ Для удаления занятий напишите их номера через запятую.

Например: 1, 3, 5

Или нажмите "🔙 Назад" для отмены
        """
    
    def handle_message(self, user_id: int, message: str) -> str:
        state = self._get_state(user_id)
        
        logger.debug(f"User {user_id} in state {state.value}, message: {message[:50]}")
        
        if state == BotState.ASKING_NAME:
            return self._handle_name_input(user_id, message)
        
        elif state == BotState.ASKING_DAYS:
            return self._handle_days_input(user_id, message)
        
        elif state == BotState.CONFIRMING_SCHEDULE:
            return self._handle_schedule_confirmation(user_id, message)
        
        elif state == BotState.ADJUSTING_SLOTS:
            return self._handle_slot_adjustment(user_id, message)
        
        else:
            return BotMessages.UNKNOWN_COMMAND
    
    def _handle_name_input(self, user_id: int, name: str) -> str:
        valid, error = Validator.validate_name(name)
        if not valid:
            return BotMessages.error_validation(error)
    
        self.expert_ctrl.update_expert_name(user_id, name)
        
        self._set_state(user_id, BotState.ASKING_DAYS)
        
        return BotMessages.confirm_name(name) + "\n\n" + BotMessages.ASK_DAYS
    
    def _handle_days_input(self, user_id: int, days_text: str) -> str:
        success, error, weekdays = self.expert_ctrl.set_expert_preferences(
            user_id, days_text
        )
        
        if not success:
            return BotMessages.error_validation(error)
        
        expert = self.expert_ctrl.get_expert(user_id)
        if not expert:
            return BotMessages.ERROR_GENERAL
        
        session = self._get_session_data(user_id)
        session['selected_slots'] = []
        
        self._set_state(user_id, BotState.SELECTING_DATE)
        
        return """
📅 Отлично! Теперь выберите даты для занятий.

Выберите месяц из кнопок ниже:
        """
    
    def get_free_slots_for_date(self, user_id: int, selected_date) -> list:
        """Получить свободные слоты на выбранную дату"""
        from config.constants import TIME_SLOTS
        from datetime import datetime, time
        
        free_slots = []
        
        all_free_slots = self.schedule_ctrl.schedule.get_free_slots()
        
        slots_on_date = [slot for slot in all_free_slots if slot.slot_date == selected_date]
        
        for time_slot in TIME_SLOTS:
            start_time_str, end_time_str = time_slot.split('-')
            start_hour, start_min = map(int, start_time_str.split(':'))
            
            for slot in slots_on_date:
                if (slot.start_time.hour == start_hour and 
                    slot.start_time.minute == start_min):
                    free_slots.append({
                        'time_slot': time_slot,
                        'slot': slot
                    })
                    break
        
        return free_slots
    
    def add_selected_slot(self, user_id: int, slot) -> str:
        """Добавить выбранный слот в список"""
        session = self._get_session_data(user_id)
        
        if 'selected_slots' not in session:
            session['selected_slots'] = []
        
        session['selected_slots'].append(slot)
        expert = self.expert_ctrl.get_expert(user_id)
        
        slot.book(user_id, expert.name)
        
        count = len(session['selected_slots'])
        
        return f"""
✅ Слот добавлен!

📅 {slot.slot_date.strftime('%d.%m.%Y')} 
⏰ {slot.format_time_range()}

Всего выбрано: {count} занятий

Хотите добавить ещё или завершить выбор?
        """
    
    def finalize_schedule(self, user_id: int) -> str:
        """Завершить выбор и показать итоговое расписание"""
        session = self._get_session_data(user_id)
        slots = session.get('selected_slots', [])
        
        if not slots:
            return "❌ Вы не выбрали ни одного занятия. Выберите даты и время."
        
        from views.formatters import ScheduleFormatter
        formatted_schedule = ScheduleFormatter.format_confirmation_request(slots)
        
        self._set_state(user_id, BotState.CONFIRMING_SCHEDULE)
        session['draft_slots'] = slots
        
        expert = self.expert_ctrl.get_expert(user_id)
        days_list = expert.get_preferred_weekday_names()
        
        return (
            BotMessages.confirm_days(days_list) +
            "\n\n" + BotMessages.DRAFT_HEADER +
            "\n\n" + formatted_schedule +
            "\n\n" + BotMessages.ASK_CONFIRM_SCHEDULE
        )
    
    def _generate_schedule_draft(self, user_id: int, expert: Expert) -> str:
        session = self._get_session_data(user_id)
        sessions_count = session.get('sessions_count', 10)
        
        logger.info(f"Generating draft for {expert.name}, {sessions_count} sessions")
        
        slots = self.schedule_ctrl.find_slots_for_expert(
            expert=expert,
            sessions_count=sessions_count,
            distribute_evenly=True
        )
        
        if not slots:
            return BotMessages.ERROR_NO_FREE_SLOTS
        
        if len(slots) < sessions_count:
            logger.warning(f"Found only {len(slots)} slots instead of {sessions_count}")

        self.schedule_ctrl.book_slots_for_expert(slots, expert)
        
        session['draft_slots'] = slots
        
        formatted_schedule = ScheduleFormatter.format_confirmation_request(slots)
        
        self._set_state(user_id, BotState.CONFIRMING_SCHEDULE)
        
        days_list = expert.get_preferred_weekday_names()
        
        return (
            BotMessages.confirm_days(days_list) +
            "\n\n" + BotMessages.DRAFT_HEADER +
            "\n\n" + formatted_schedule +
            "\n\n" + BotMessages.ASK_CONFIRM_SCHEDULE
        )
    
    def _handle_schedule_confirmation(self, user_id: int, message: str) -> str:
        valid, answer, error = Validator.validate_yes_no(message)
        
        if not valid:
            return BotMessages.error_validation(error)
        
        expert = self.expert_ctrl.get_expert(user_id)
        session = self._get_session_data(user_id)
        slots = session.get('draft_slots', [])
        
        if not expert or not slots:
            return BotMessages.ERROR_GENERAL
        
        if answer:
            return self._confirm_and_save_schedule(user_id, expert, slots)
        else:
            self._set_state(user_id, BotState.ADJUSTING_SLOTS)
            return BotMessages.ASK_PROBLEMATIC_SLOTS
    
    def _confirm_and_save_schedule(
        self,
        user_id: int,
        expert: Expert,
        slots: List[TimeSlot]
    ) -> str:
        try:
            self.schedule_ctrl.confirm_slots_for_expert(slots, expert)
            
            if not self.schedule_ctrl.save_schedule():
                logger.error("Failed to save schedule")
                return BotMessages.ERROR_GENERAL

            if not self.expert_ctrl.save_experts():
                logger.error("Failed to save expert data")
            
            self._set_state(user_id, BotState.COMPLETED)
            
            logger.info(f"Schedule confirmed and saved for {expert.name}")
            
            return BotMessages.SUCCESS + "\n\n" + BotMessages.SAVED
            
        except Exception as e:
            logger.error(f"Error saving schedule: {e}", exc_info=True)
            return BotMessages.ERROR_GENERAL
    
    def _handle_slot_adjustment(self, user_id: int, message: str) -> str:
        session = self._get_session_data(user_id)
        slots = session.get('draft_slots', [])
        
        if not slots:
            return BotMessages.ERROR_GENERAL
        
        valid, slot_numbers, error = Validator.validate_slot_numbers(
            message, len(slots)
        )
        
        if not valid:
            return BotMessages.error_validation(error)
        
        expert = self.expert_ctrl.get_expert(user_id)
        if not expert:
            return BotMessages.ERROR_GENERAL
        
        alternatives_info = []
        
        for slot_num in slot_numbers:
            original_slot = slots[slot_num - 1]
            
            self.schedule_ctrl.get_schedule().release_slot(original_slot, expert)
            
            alternatives = self.schedule_ctrl.find_alternatives(
                original_slot, expert, count=3
            )
            
            if alternatives:
                new_slot = alternatives[0]
                self.schedule_ctrl.get_schedule().book_slot(new_slot, expert)
                slots[slot_num - 1] = new_slot
                
                alt_text = ScheduleFormatter.format_alternatives(
                    original_slot, alternatives
                )
                alternatives_info.append(alt_text)
            else:
                alternatives_info.append(
                    f"Для слота #{slot_num} не найдено альтернатив"
                )
        
        session['draft_slots'] = slots
        
        formatted_schedule = ScheduleFormatter.format_confirmation_request(slots)
        
        self._set_state(user_id, BotState.CONFIRMING_SCHEDULE)
        
        return (
            "\n\n".join(alternatives_info) +
            "\n\n📋 Обновлённое расписание:\n\n" +
            formatted_schedule +
            "\n\n" + BotMessages.ASK_CONFIRM_SCHEDULE
        )
    
    
    def get_user_state(self, user_id: int) -> BotState:
        return self._get_state(user_id)
    
    def get_statistics(self) -> Dict:
        schedule_stats = self.schedule_ctrl.get_schedule_statistics()
        experts_count = self.expert_ctrl.get_experts_count()
        
        return {
            "schedule": schedule_stats,
            "experts_count": experts_count,
            "active_sessions": len(self.session_data)
        }
    
    def cleanup(self) -> None:
        logger.info("Cleaning up BotController")
        self.schedule_ctrl.close()
        self.user_states.clear()
        self.session_data.clear()
