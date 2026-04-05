import logging
from openseek import DeepSeek

logger = logging.getLogger(__name__)

_deepseek_client = None

async def get_deepseek_client():
    global _deepseek_client
    if _deepseek_client is None:
        from config import DEEPSEEK_EMAIL, DEEPSEEK_PASSWORD
        if not DEEPSEEK_EMAIL or not DEEPSEEK_PASSWORD:
            raise Exception("DEEPSEEK_EMAIL и DEEPSEEK_PASSWORD не заданы в переменных окружения!")
        logger.info("Инициализация DeepSeek клиента...")
        _deepseek_client = DeepSeek(
            email=DEEPSEEK_EMAIL,
            password=DEEPSEEK_PASSWORD,
            headless=True
        )
        await _deepseek_client.initialize()
        logger.info("DeepSeek клиент готов.")
    return _deepseek_client

async def get_lyrics(messages_history: list) -> str:
    client = await get_deepseek_client()
    # Ищем последнее сообщение пользователя
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")
    response = await client.send_message(last_user_msg)
    return response.text
