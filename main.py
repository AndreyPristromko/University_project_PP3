import sys
from controllers.bot_controller import BotController
from controllers.schedule_controller import ScheduleController
from controllers.expert_controller import ExpertController
from services.telegram_service import TelegramService
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


def initialize_application() -> BotController:
    try:
        logger.info("=" * 60)
        logger.info("Запуск приложения: Бот-составитель расписания")
        logger.info("=" * 60)
        
        logger.info("Создание контроллеров...")
        schedule_controller = ScheduleController()
        expert_controller = ExpertController()
        
        bot_controller = BotController(
            schedule_controller=schedule_controller,
            expert_controller=expert_controller
        )
        
        logger.info("Инициализация контроллеров...")
        if not bot_controller.initialize():
            logger.error("Не удалось инициализировать BotController")
            return None
        
        logger.info("✅ Приложение успешно инициализировано")
        logger.info("=" * 60)
        
        return bot_controller
        
    except Exception as e:
        logger.error(f"Критическая ошибка при инициализации: {e}", exc_info=True)
        return None


def run_telegram_bot(bot_controller: BotController) -> None:
    try:
        logger.info("Запуск Telegram бота...")
        
        token = Settings.TELEGRAM_BOT_TOKEN
        if not token or token == "your_bot_token_here":
            logger.error("TELEGRAM_BOT_TOKEN не установлен в файле .env")
            print("\n❌ Ошибка: Не указан токен Telegram бота")
            print("\nИнструкция:")
            print("1. Создайте бота через @BotFather в Telegram")
            print("2. Скопируйте токен")
            print("3. Добавьте токен в файл .env:")
            print("   TELEGRAM_BOT_TOKEN=your_token_here")
            return
        
        telegram_service = TelegramService(token, bot_controller)
        
        telegram_service.setup()
        
        show_statistics(bot_controller)
        
        print("\n" + "=" * 60)
        print("🤖 Telegram бот запущен!")
        print("=" * 60)
        print("Откройте Telegram и найдите вашего бота")
        print("Отправьте команду /start для начала работы")
        print("\nДля остановки нажмите Ctrl+C")
        print("=" * 60 + "\n")
        
        telegram_service.run()
        
    except KeyboardInterrupt:
        logger.info("Остановка по запросу пользователя")
        print("\n\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")


def show_statistics(bot: BotController) -> None:
    try:
        stats = bot.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ПРИЛОЖЕНИЯ")
        print("=" * 60)
        
        print(f"\n📅 Расписание:")
        schedule_stats = stats.get('schedule', {})
        print(f"  • Всего слотов: {schedule_stats.get('total', 0)}")
        print(f"  • Свободно: {schedule_stats.get('free', 0)}")
        print(f"  • Занято: {schedule_stats.get('booked', 0)}")
        print(f"  • Загруженность: {schedule_stats.get('utilization_percent', 0)}%")
        
        print(f"\n👥 Эксперты:")
        print(f"  • Всего экспертов: {stats.get('experts_count', 0)}")
        
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}", exc_info=True)


def main():
    bot_controller = initialize_application()
    
    if not bot_controller:
        logger.error("Не удалось запустить приложение")
        sys.exit(1)
    
    try:
        run_telegram_bot(bot_controller)
        
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Завершение работы приложения")
        bot_controller.cleanup()
        logger.info("Приложение завершено")


if __name__ == "__main__":
    main()
