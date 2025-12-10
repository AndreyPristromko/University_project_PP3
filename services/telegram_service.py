from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from controllers.bot_controller import BotController
from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramService:
    def __init__(self, token: str, bot_controller: BotController):
        self.token = token
        self.bot_controller = bot_controller
        self.application = None
        
        logger.info("TelegramService инициализирован")
    
    def setup(self) -> Application:
        try:
            self.application = Application.builder().token(self.token).build()
            
            self.application.add_handler(
                CommandHandler("start", self.handle_start_command)
            )
            self.application.add_handler(
                CommandHandler("help", self.handle_help_command)
            )
            self.application.add_handler(
                CommandHandler("cancel", self.handle_cancel_command)
            )
            self.application.add_handler(
                CommandHandler("edit_schedule", self.handle_edit_schedule_command)
            )
            self.application.add_handler(
                CommandHandler("menu", self.handle_menu_command)
            )
            
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            self.application.add_handler(
                CallbackQueryHandler(self.handle_callback)
            )
            
            logger.info("Обработчики Telegram зарегистрированы")
            return self.application
            
        except Exception as e:
            logger.error(f"Ошибка настройки TelegramService: {e}", exc_info=True)
            raise
    
    async def handle_start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} sent /start")
        
        response = self.bot_controller.handle_start(user_id)
        
        reply_markup = self.get_main_menu_keyboard()
        
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    async def handle_help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} sent /help")
        
        response = self.bot_controller.handle_help(user_id)
        await update.message.reply_text(response)
    
    async def handle_cancel_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} sent /cancel")
        
        response = self.bot_controller.handle_cancel(user_id)
        
        keyboard = [
            ["📅 Создать новое расписание"],
            ["✏️ Изменить расписание", "❓ Помощь"],
            ["❌ Отмена"]
        ]
        reply_markup = self.create_keyboard(keyboard, persistent=True)
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    async def handle_edit_schedule_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} sent /edit_schedule")
        
        response = self.bot_controller.handle_edit_schedule(user_id)
        await update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())
    
    async def handle_menu_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} sent /menu")
        
        keyboard = [
            ["📅 Создать новое расписание"],
            ["✏️ Изменить расписание", "❓ Помощь"],
            ["❌ Отмена"]
        ]
        reply_markup = self.create_keyboard(keyboard, persistent=True)
        
        await update.message.reply_text(
            "Главное меню. Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        logger.info(f"User {user_id} pressed button: {callback_data}")
        
        if callback_data == "new_schedule":
            response = self.bot_controller.handle_new_schedule(user_id)
            await query.edit_message_text(response)
        
        elif callback_data == "select_month":
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            today = datetime.now()
            keyboard = []
            months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            
            for i in range(3):
                month_date = today + relativedelta(months=i)
                month_name = months_ru[month_date.month - 1]
                keyboard.append([InlineKeyboardButton(
                    f"📅 {month_name} {month_date.year}", 
                    callback_data=f"month_{month_date.strftime('%Y-%m')}"
                )])
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📅 Выберите месяц для занятий:",
                reply_markup=reply_markup
            )
        
        elif callback_data.startswith("month_"):
            from datetime import datetime, timedelta
            import calendar
            
            month_str = callback_data.replace("month_", "")
            year, month = map(int, month_str.split("-"))
            
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            
            months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            
            keyboard = []
            current_week_start = first_day
            week_num = 1
            
            while current_week_start.date() <= last_day.date():
                week_end = current_week_start + timedelta(days=6)
                if week_end.date() > last_day.date():
                    week_end = datetime.combine(last_day.date(), datetime.min.time())
                
                keyboard.append([InlineKeyboardButton(
                    f"Неделя {week_num}: {current_week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}",
                    callback_data=f"week_{current_week_start.strftime('%Y-%m-%d')}"
                )])
                
                current_week_start = current_week_start + timedelta(days=7)
                week_num += 1
            
            keyboard.append([InlineKeyboardButton("🔙 Назад к месяцам", callback_data="select_month")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📅 Выберите неделю в {months_ru[month-1]} {year}:",
                reply_markup=reply_markup
            )
        
        elif callback_data.startswith("week_"):
            from datetime import datetime, timedelta
            
            week_start_str = callback_data.replace("week_", "")
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            
            expert = self.bot_controller.expert_ctrl.get_expert(user_id)
            preferred_weekdays = expert.preferred_weekdays if expert else []
            
            days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            
            keyboard = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_name = days_ru[day.weekday()]
                
                from config.constants import Weekday
                weekday_num = day.weekday()
                weekday_names = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
                day_enum_name = weekday_names[weekday_num]
                
                is_preferred = any(wd.name == day_enum_name for wd in preferred_weekdays)
                prefix = "✅ " if is_preferred else "📅 "
                
                keyboard.append([InlineKeyboardButton(
                    f"{prefix}{day.strftime('%d.%m')} ({day_name})",
                    callback_data=f"day_{day.strftime('%Y-%m-%d')}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад к неделям", callback_data=f"month_{week_start.strftime('%Y-%m')}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📅 Выберите день:\n✅ - ваши предпочитаемые дни",
                reply_markup=reply_markup
            )
        
        elif callback_data.startswith("day_"):
            from datetime import datetime, timedelta
            
            day_str = callback_data.replace("day_", "")
            selected_date = datetime.strptime(day_str, '%Y-%m-%d').date()
            
            free_slots = self.bot_controller.get_free_slots_for_date(user_id, selected_date)
            
            if not free_slots:
                await query.answer("❌ На эту дату нет свободных слотов", show_alert=True)
                week_start = selected_date - timedelta(days=selected_date.weekday())
                keyboard = [[InlineKeyboardButton("🔙 Назад к дням", callback_data=f"week_{week_start.strftime('%Y-%m-%d')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"❌ На {selected_date.strftime('%d.%m.%Y')} нет свободных слотов.\nВыберите другой день.",
                    reply_markup=reply_markup
                )
                return
            
            keyboard = []
            for slot_info in free_slots:
                time_slot = slot_info['time_slot']
                keyboard.append([InlineKeyboardButton(
                    f"🕐 {time_slot}",
                    callback_data=f"slot_{selected_date.strftime('%Y-%m-%d')}_{time_slot}"
                )])
            
            week_start = selected_date - timedelta(days=selected_date.weekday())
            
            keyboard.append([InlineKeyboardButton("🔙 Назад к дням", callback_data=f"week_{week_start.strftime('%Y-%m-%d')}")])
            keyboard.append([InlineKeyboardButton("✅ Завершить выбор", callback_data="finalize_schedule")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📅 {selected_date.strftime('%d.%m.%Y')}\n\n⏰ Выберите свободное время ({len(free_slots)} слотов):",
                reply_markup=reply_markup
            )
        
        elif callback_data.startswith("slot_"):
            parts = callback_data.replace("slot_", "").split("_")
            date_str = parts[0]
            time_slot = "_".join(parts[1:])
            
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            free_slots = self.bot_controller.get_free_slots_for_date(user_id, selected_date)
            selected_slot = None
            
            for slot_info in free_slots:
                if slot_info['time_slot'] == time_slot:
                    selected_slot = slot_info['slot']
                    break
            
            if selected_slot:
                response = self.bot_controller.add_selected_slot(user_id, selected_slot)
                
                keyboard = [
                    [InlineKeyboardButton("➕ Добавить ещё занятие", callback_data="select_month")],
                    [InlineKeyboardButton("✅ Завершить и сохранить", callback_data="finalize_schedule")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(response, reply_markup=reply_markup)
            else:
                await query.answer("❌ Слот не найден", show_alert=True)
        
        elif callback_data == "finalize_schedule":
            response = self.bot_controller.finalize_schedule(user_id)
            
            keyboard = [
                [InlineKeyboardButton("✅ Да, сохранить", callback_data="confirm_final")],
                [InlineKeyboardButton("➕ Добавить ещё", callback_data="select_month")],
                [InlineKeyboardButton("❌ Отменить всё", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
        
        elif callback_data == "confirm_final":
            session = self.bot_controller._get_session_data(user_id)
            slots = session.get('selected_slots', [])
            expert = self.bot_controller.expert_ctrl.get_expert(user_id)
            
            if slots and expert:
                response = self.bot_controller._confirm_and_save_schedule(
                    user_id, expert, slots
                )
                
                reply_markup = self.get_main_menu_keyboard()
                await query.edit_message_text(response, reply_markup=reply_markup)
            else:
                await query.answer("❌ Ошибка: нет выбранных слотов", show_alert=True)
        
        elif callback_data == "view_schedule":
            response = self.bot_controller.handle_edit_schedule(user_id)
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
            
        elif callback_data == "edit_schedule":
            response = self.bot_controller.handle_edit_schedule(user_id)
            keyboard = [
                [InlineKeyboardButton("➕ Добавить занятие", callback_data="add_lesson")],
                [InlineKeyboardButton("🗑️ Удалить занятия", callback_data="delete_lessons")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
        
        elif callback_data == "add_lesson":
            response = self.bot_controller.handle_add_lesson(user_id)
            from datetime import datetime, timedelta
            keyboard = []
            today = datetime.now().date()
            for i in range(0, 14, 2): 
                date1 = today + timedelta(days=i)
                date2 = today + timedelta(days=i+1)
                row = [
                    InlineKeyboardButton(
                        f"{date1.strftime('%d.%m (%a)')}", 
                        callback_data=f"date_{date1.strftime('%Y-%m-%d')}"
                    ),
                    InlineKeyboardButton(
                        f"{date2.strftime('%d.%m (%a)')}", 
                        callback_data=f"date_{date2.strftime('%Y-%m-%d')}"
                    )
                ]
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="edit_schedule")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
        
        elif callback_data.startswith("date_"):
            date_str = callback_data.replace("date_", "")
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            session = self.bot_controller._get_session_data(user_id)
            session['selected_date'] = selected_date
            
            from config.constants import TIME_SLOTS
            keyboard = []
            for i in range(0, len(TIME_SLOTS), 2):
                row = []
                for j in range(2):
                    if i + j < len(TIME_SLOTS):
                        time_slot = TIME_SLOTS[i + j]
                        row.append(InlineKeyboardButton(
                            f"🕐 {time_slot}", 
                            callback_data=f"time_{time_slot}"
                        ))
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="add_lesson")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📅 Выбрана дата: {selected_date.strftime('%d.%m.%Y')}\n\n⏰ Выберите время:",
                reply_markup=reply_markup
            )
        
        elif callback_data.startswith("time_"):
            time_slot = callback_data.replace("time_", "")
            session = self.bot_controller._get_session_data(user_id)
            selected_date = session.get('selected_date')
            
            if selected_date:
                await query.edit_message_text(
                    f"✅ Занятие добавлено:\n📅 {selected_date.strftime('%d.%m.%Y')}\n⏰ {time_slot}\n\nВозвращайтесь в меню для дальнейших действий.",
                )
                keyboard = [
                    [InlineKeyboardButton("📅 Создать новое расписание", callback_data="new_schedule")],
                    [
                        InlineKeyboardButton("✏️ Изменить расписание", callback_data="edit_schedule"),
                        InlineKeyboardButton("❓ Помощь", callback_data="help")
                    ],
                    [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text("Главное меню:", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ Ошибка: дата не выбрана")
        
        elif callback_data == "delete_lessons":
            response = self.bot_controller.handle_delete_lessons(user_id)
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="edit_schedule")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
            
        elif callback_data == "help":
            response = self.bot_controller.handle_help(user_id)
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, reply_markup=reply_markup)
            
        elif callback_data == "cancel":
            response = self.bot_controller.handle_cancel(user_id)
            reply_markup = self.get_main_menu_keyboard()
            await query.edit_message_text(response, reply_markup=reply_markup)
            
        elif callback_data == "menu":
            reply_markup = self.get_main_menu_keyboard()
            await query.edit_message_text(
                "Главное меню. Выберите действие:",
                reply_markup=reply_markup
            )
    
    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.debug(f"User {user_id} sent message: {message_text[:50]}")
        
        if message_text == "📅 Создать новое расписание":
            response = self.bot_controller.handle_new_schedule(user_id)
            await update.message.reply_text(response)
            return
        
        elif message_text == "✏️ Изменить расписание":
            response = self.bot_controller.handle_edit_schedule(user_id)
            await update.message.reply_text(response)
            return
        
        elif message_text == "❓ Помощь":
            response = self.bot_controller.handle_help(user_id)
            keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(response, reply_markup=reply_markup)
            return
        
        elif message_text == "❌ Отмена":
            response = self.bot_controller.handle_cancel(user_id)
            reply_markup = self.get_main_menu_keyboard()
            await update.message.reply_text(response, reply_markup=reply_markup)
            return
        
        response = self.bot_controller.handle_message(user_id, message_text)
        
        from config.constants import BotState
        state = self.bot_controller.get_user_state(user_id)
        
        if state == BotState.SELECTING_DATE:
            keyboard = [[InlineKeyboardButton("📅 Выбрать даты", callback_data="select_month")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            await update.message.reply_text(response)
    
    def run(self) -> None:
        try:
            logger.info("Запуск Telegram бота...")
            logger.info("Бот готов к работе! Нажмите Ctrl+C для остановки.")
            
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
            raise
    
    def stop(self) -> None:
        if self.application:
            logger.info("Остановка Telegram бота")
            self.application.stop()
    
    @staticmethod
    def create_keyboard(buttons: list, persistent: bool = False) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(btn) for btn in row] for row in buttons]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=not persistent,
            is_persistent=persistent
        )
    
    @staticmethod
    def get_main_menu_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("📅 Создать новое расписание", callback_data="new_schedule")],
            [InlineKeyboardButton("📋 Просмотреть моё расписание", callback_data="view_schedule")],
            [
                InlineKeyboardButton("✏️ Изменить расписание", callback_data="edit_schedule"),
                InlineKeyboardButton("❓ Помощь", callback_data="help")
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
