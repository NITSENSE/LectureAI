import logging
from typing import Optional
from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL, PROXY_URL

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Клиент для работы с Google Gemini API через новый SDK (google-genai).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = GEMINI_MODEL,
        proxy: Optional[str] = None
    ):
        """
        Инициализация клиента Gemini.
        
        Args:
            api_key: API ключ Gemini (если None, берется из настроек)
            model_name: Название модели
            proxy: URL прокси (опционально)
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name
        self.proxy = proxy or PROXY_URL 
        self.client = None
        
        self._configure()
    
    def _configure(self) -> None:
        """Настройка API клиента и прокси."""
        if not self.api_key:
            logger.warning("API ключ Gemini не установлен")
            return
        
        http_options = None
        

        if self.proxy:
            http_options = types.HttpOptions(
                client_args={'proxy': self.proxy},
                async_client_args={'proxy': self.proxy}
            )
            logger.info(f"Используется прокси (изолированно для клиента Gemini): {self.proxy}")
        
        try:
            self.client = genai.Client(
                api_key=self.api_key,
                http_options=http_options
            )
            logger.info(f"Gemini API клиент настроен, модель: {self.model_name}")
        except Exception as e:
            logger.error(f"Ошибка настройки Gemini API: {e}", exc_info=True)
    
    def generate(self, prompt: str) -> Optional[str]:
        """
        Генерация текста с помощью Gemini.
        
        Args:
            prompt: Текст промпта
            
        Returns:
            Сгенерированный текст или None
        """
        if not self.client:
            logger.error("Клиент Gemini не инициализирован")
            return None
        
        try:
            logger.info(f"Отправка запроса к Gemini (длина промпта: {len(prompt)} символов)")
            

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            

            try:
                text = response.text
                if text:
                    logger.info(f"Получен ответ ({len(text)} символов)")
                    return text
                else:
                    if response.candidates:
                        finish_reason = response.candidates[0].finish_reason
                        logger.warning(f"Пустой ответ от Gemini. Причина завершения: {finish_reason}")
                    else:
                        logger.warning("Пустой ответ от Gemini (отсутствуют кандидаты)")
                    return None
            except ValueError:
                safety_ratings = "Неизвестно"
                if response.candidates and hasattr(response.candidates[0], 'safety_ratings'):
                    safety_ratings = response.candidates[0].safety_ratings
                logger.warning(f"Ответ заблокирован фильтрами безопасности. Статус: {safety_ratings}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при генерации: {e}", exc_info=True)
            return None

    # Если вы работаете в асинхронном фреймворке (напр. Aiogram или FastAPI):
    async def generate_async(self, prompt: str) -> Optional[str]:
        """Асинхронная генерация текста с помощью Gemini."""
        if not self.client:
            logger.error("Клиент Gemini не инициализирован")
            return None
            
        try:
            logger.info(f"[ASYNC] Отправка запроса к Gemini (длина: {len(prompt)})")
            
            # Асинхронные вызовы в новом SDK находятся в пространстве .aio
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            try:
                text = response.text
                if text:
                    return text
                else:
                    if response.candidates:
                        logger.warning(f"[ASYNC] Пустой ответ. Причина: {response.candidates[0].finish_reason}")
                    return None
            except ValueError:
                logger.warning("[ASYNC] Ответ заблокирован фильтрами безопасности.")
                return None
        except Exception as e:
            logger.error(f"Ошибка при асинхронной генерации: {e}", exc_info=True)
            return None
    
    def generate_with_context(
        self,
        prompt: str,
        context: str,
        max_context_length: int = 100000
    ) -> Optional[str]:
        """
        Генерация текста с контекстом.
        """
        if len(context) > max_context_length:
            logger.warning(f"Контекст обрезан с {len(context)} до {max_context_length} символов")
            context = context[:max_context_length]
        
        full_prompt = f"Контекст:\n{context}\n\nЗадача: {prompt}"
        return self.generate(full_prompt)
    
    def test_connection(self) -> bool:
        """
        Тестирование соединения с API.
        """
        if not self.client:
            return False
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Say 'OK'"
            )
            try:
                return bool(response.text)
            except ValueError:
                return True
        except Exception as e:
            logger.error(f"Ошибка тестирования соединения: {e}")
            return False