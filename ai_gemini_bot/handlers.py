# handlers.py - обработчики команд и сообщений
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from gemini_api import GeminiAPI
from firebase_service import DatabaseService
from utils.formatter import format_code, escape_markdown
from utils.chunker import split_message
from config import FREE_DAILY_LIMIT, PREMIUM_PRICES, ADMIN_IDS
import logging

logger = logging.getLogger(__name__)


class BotHandlers:
    def __init__(self):
        self.gemini = GeminiAPI()
        self.db = DatabaseService()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Регистрация/получение пользователя
        user = self.db.get_user(user_id)
        if not user:
            self.db.create_user(user_id, username)
            user = self.db.get_user(user_id)
        
        # Формируем информацию о тарифе
        plan_info = self._get_plan_info(user)
        
        keyboard = [
            [InlineKeyboardButton("🎁 Промокод", callback_data="promo")],
            [InlineKeyboardButton("⭐ Купить Premium", callback_data="upgrade")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome = f"""👋 Привет! Я — Gemini AI Chat.

{plan_info}

💬 Просто напиши мне что угодно, и я отвечу!

🔧 Команды:
/promo - ввести промокод
/upgrade - купить премиум
/stats - статистика
/clear - очистить историю"""
        
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    
    def _get_plan_info(self, user):
        """Информация о тарифе"""
        plan = user['plan']
        
        if plan == 'vip':
            return """🎁 Ваш тариф: 💎 VIP (Навсегда)
✨ Безлимитные запросы
🚀 Приоритет обработки"""
        
        elif plan == 'premium':
            if user['premium_expires']:
                expires = datetime.fromisoformat(user['premium_expires'])
                days = (expires - datetime.now()).days
                
                if days > 0:
                    return f"""⭐ Ваш тариф: Premium
📅 Осталось дней: {days}
✨ Безлимитные запросы"""
        
        # Free план
        remaining = self.db.get_remaining_requests(user['user_id'])
        return f"""🎁 Ваш тариф: Бесплатный
📊 Осталось запросов: {remaining}/{FREE_DAILY_LIMIT}
💡 Хотите больше? → /upgrade"""
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Получение пользователя
        user = self.db.get_user(user_id)
        if not user:
            await update.message.reply_text("⚠️ Нажмите /start для начала")
            return
        
        # Проверка лимита запросов
        remaining = self.db.get_remaining_requests(user_id)
        if remaining <= 0:
            keyboard = [[InlineKeyboardButton("⭐ Купить Premium", callback_data="upgrade")]]
            await update.message.reply_text(
                "❌ Ваш дневной лимит исчерпан.\n\n"
                "Хотите разблокировать безлимит? → /upgrade",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Показать "печатает..."
        await update.message.chat.send_action("typing")
        
        try:
            # Получить историю диалога
            history = self.db.get_conversation_history(user_id)
            
            # Генерация ответа
            ai_response = self.gemini.generate_response(message_text, history)
            
            # Форматирование ответа
            formatted_response = format_code(ai_response)
            
            # Разбивка на части, если слишком длинный
            chunks = split_message(formatted_response)
            
            # Отправка ответа
            for chunk in chunks:
                await update.message.reply_text(
                    chunk,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
            # Сохранение в историю
            self.db.save_message(user_id, 'user', message_text)
            self.db.save_message(user_id, 'assistant', ai_response)
            
            # Уменьшение лимита для free
            if user['plan'] == 'free':
                self.db.use_request(user_id)
                
                # Показать оставшиеся запросы
                remaining = self.db.get_remaining_requests(user_id)
                if remaining <= 3:
                    await update.message.reply_text(
                        f"⚠️ Осталось запросов сегодня: {remaining}"
                    )
        
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "😔 Произошла ошибка. Попробуйте ещё раз или /clear историю."
            )
    
    async def promo_activate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Активация промокода"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🎁 Введите промокод:\n\n"
                "Пример: `/promo VIP-FOREVER`",
                parse_mode='Markdown'
            )
            return
        
        promo_code = context.args[0].upper()
        result = self.db.activate_promocode(user_id, promo_code)
        
        if result['success']:
            promo = result['promo']
            msg = "🎉 Промокод активирован!\n\n"
            
            if promo['type'] == 'vip':
                msg += "✨ Ваш тариф: 💎 VIP\n⏰ Срок: НАВСЕГДА"
            elif promo['type'] == 'premium':
                msg += f"⭐ Ваш тариф: Premium\n⏰ Срок: {promo['days']} дней"
            elif promo['type'] == 'requests':
                msg += f"📊 Добавлено запросов: +{promo['requests']}"
            
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(f"❌ {result['error']}")
    
    async def upgrade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню покупки премиума"""
        keyboard = [
            [InlineKeyboardButton(f"⭐ Premium 7 дней - ${PREMIUM_PRICES[7]}", callback_data="buy_premium_7")],
            [InlineKeyboardButton(f"⭐ Premium 30 дней - ${PREMIUM_PRICES[30]}", callback_data="buy_premium_30")],
            [InlineKeyboardButton(f"⭐ Premium 90 дней - ${PREMIUM_PRICES[90]}", callback_data="buy_premium_90")],
            [InlineKeyboardButton(f"💎 VIP Навсегда - ${PREMIUM_PRICES['vip']}", callback_data="buy_vip")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """⭐ ТАРИФНЫЕ ПЛАНЫ

🟢 Бесплатный (текущий)
• 10 запросов в день
• Базовая скорость

⭐ Premium
• ♾️ Безлимитные запросы
• ⚡ Быстрые ответы
• 🧠 Gemini 2.0 Flash
• 📝 Длинная память

💎 VIP (лучший выбор!)
• Всё из Premium
• ⏰ НАВСЕГДА без подписки
• 🎯 Эксклюзивные функции

Выберите план:"""
        
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика пользователя"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await update.message.reply_text("⚠️ Нажмите /start")
            return
        
        stats = self.db.get_user_stats(user_id)
        remaining = self.db.get_remaining_requests(user_id)
        
        text = f"""📊 Ваша статистика

👤 ID: {user_id}
📝 Тариф: {user['plan'].upper()}
💬 Всего сообщений: {stats['total_messages']}
📊 Осталось запросов: {remaining if user['plan'] == 'free' else '∞'}
📅 Регистрация: {user['created_at'][:10]}"""
        
        await update.message.reply_text(text)
    
    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка истории диалога"""
        user_id = update.effective_user.id
        self.db.clear_history(user_id)
        
        await update.message.reply_text(
            "🗑️ История диалога очищена!\n\n"
            "Начнём с чистого листа 😊"
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "promo":
            await query.message.reply_text(
                "🎁 Введите промокод:\n\n"
                "Пример: `/promo VIP-FOREVER`",
                parse_mode='Markdown'
            )
        
        elif query.data == "upgrade":
            await self.upgrade(update, context)
        
        elif query.data == "stats":
            await self.stats(update, context)
        
        elif query.data == "help":
            await query.message.reply_text(
                "ℹ️ ПОМОЩЬ\n\n"
                "🔧 Команды:\n"
                "/start - главное меню\n"
                "/promo - ввести промокод\n"
                "/upgrade - купить премиум\n"
                "/stats - статистика\n"
                "/clear - очистить историю\n\n"
                "💬 Просто пишите мне вопросы, и я отвечу!"
            )
        
        elif query.data.startswith("buy_"):
            await query.message.reply_text(
                "💳 Для покупки свяжитесь с админом:\n@your_admin\n\n"
                "Или используйте промокод: /promo КОД"
            )