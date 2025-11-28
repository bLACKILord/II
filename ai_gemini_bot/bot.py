# bot.py - главный файл запуска бота
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
from handlers import BotHandlers
from gemini_api import GeminiAPI # Импортируем класс GeminiAPI

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота...")

    # Проверка подключения к Gemini API
    logger.info("🔄 Проверка подключения к Gemini API...")
    gemini_tester = GeminiAPI() # Создаем временный объект для теста
    if not gemini_tester.test_connection():
        logger.error("❌ Не удалось подключиться к Gemini. Проверьте ваш GEMINI_API_KEY в config.py")
        return # Останавливаем запуск, если ключ неверный
    
    # Создание приложения
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Инициализация обработчиков
    handlers = BotHandlers()
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("promo", handlers.promo_activate))
    app.add_handler(CommandHandler("upgrade", handlers.upgrade))
    app.add_handler(CommandHandler("stats", handlers.stats))
    app.add_handler(CommandHandler("clear", handlers.clear_history))
    
    # Обработка кнопок
    app.add_handler(CallbackQueryHandler(handlers.button_callback))
    
    # Обработка текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    
    logger.info("✅ Бот успешно запущен!")
    logger.info("📝 Нажми Ctrl+C для остановки")
    
    # Запуск polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")