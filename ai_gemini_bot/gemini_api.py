# gemini_api.py - модуль работы с Gemini API (ИСПРАВЛЕНО)
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, BOT_PERSONALITY, MAX_MESSAGE_LENGTH
import logging

logger = logging.getLogger(__name__)


class GeminiAPI:
    def __init__(self):
        """Инициализация Gemini"""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Настройки генерации для стабильности
            self.generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            # Инициализация модели с настройками
            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=self.generation_config
            )
            
            logger.info(f"✅ Gemini модель {GEMINI_MODEL} инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Gemini: {e}")
            raise
    
    def generate_response(self, message: str, history: list = None) -> str:
        """
        Генерация ответа от Gemini
        
        Args:
            message: сообщение пользователя
            history: история диалога [(role, content), ...]
        
        Returns:
            str: ответ AI
        """
        try:
            # Формируем системный промпт
            system_prompt = "\n".join(BOT_PERSONALITY)
            
            # Формируем контекст беседы
            conversation_parts = [system_prompt]
            
            # Добавляем историю (последние N сообщений)
            if history:
                for role, content in history[-6:]:  # берем последние 6 сообщений
                    prefix = "Пользователь" if role == "user" else "Ассистент"
                    conversation_parts.append(f"{prefix}: {content}")
            
            # Добавляем текущее сообщение
            conversation_parts.append(f"Пользователь: {message}")
            conversation_parts.append("Ассистент:")
            
            full_prompt = "\n\n".join(conversation_parts)
            
            # Генерируем ответ с таймаутом
            logger.info("🔄 Отправка запроса к Gemini...")
            response = self.model.generate_content(full_prompt)
            
            # Проверяем, есть ли ответ
            if not response or not response.text:
                logger.warning("⚠️ Gemini вернул пустой ответ")
                return "😔 Извините, не смог сгенерировать ответ. Попробуйте перефразировать вопрос."
            
            ai_response = response.text.strip()
            
            # Обрезаем слишком длинные ответы
            if len(ai_response) > MAX_MESSAGE_LENGTH:
                ai_response = ai_response[:MAX_MESSAGE_LENGTH] + "\n\n...(ответ обрезан)"
            
            logger.info(f"✅ Ответ получен ({len(ai_response)} символов)")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini API: {e}")
            
            # Детальные сообщения об ошибках
            error_msg = str(e).lower()
            
            if "api key" in error_msg or "invalid" in error_msg:
                return "❌ Ошибка API ключа. Проверьте GEMINI_API_KEY в config.py"
            
            elif "quota" in error_msg or "limit" in error_msg:
                return "⚠️ Превышен лимит запросов к Gemini. Попробуйте позже."
            
            elif "timeout" in error_msg:
                return "⏱️ Превышено время ожидания. Попробуйте ещё раз."
            
            elif "blocked" in error_msg or "safety" in error_msg:
                return "🛡️ Ваш запрос заблокирован фильтрами безопасности Gemini. Попробуйте перефразировать."
            
            else:
                return f"😔 Ошибка при обработке запроса: {str(e)[:100]}"
    
    def test_connection(self) -> bool:
        """Тест подключения к Gemini"""
        try:
            logger.info("🧪 Тестирование подключения к Gemini...")
            response = self.model.generate_content("Hello, respond with 'OK'")
            
            if response and response.text:
                logger.info(f"✅ Тест пройден! Ответ: {response.text[:50]}")
                return True
            else:
                logger.error("❌ Получен пустой ответ от Gemini")
                return False
                
        except Exception as e:
            logger.error(f"❌ Тест не прошёл: {e}")
            
            # Детальная диагностика
            error_msg = str(e)
            
            if "API key not valid" in error_msg:
                logger.error("🔑 Неверный API ключ!")
                logger.error(f"   Ваш ключ: {GEMINI_API_KEY[:20]}...")
                logger.error("   Получите новый: https://aistudio.google.com/apikey")
            
            elif "quota" in error_msg.lower():
                logger.error("📊 Исчерпан лимит бесплатного плана Gemini")
            
            elif "not found" in error_msg.lower():
                logger.error(f"❌ Модель {GEMINI_MODEL} не найдена")
            
            return False