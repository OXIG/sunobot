import aiohttp
import logging
from config import DEEPSEEK_API_URL

logger = logging.getLogger(__name__)

async def get_lyrics(messages_history: list) -> str:
    """
    Отправляет историю сообщений в DeepSeek через локальный прокси (deepseek-free-api)
    и возвращает текст ответа.
    """
    # Извлекаем последнее сообщение пользователя
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break

    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    if not DEEPSEEK_API_URL:
        raise Exception("DEEPSEEK_API_URL не задана в переменных окружения")

    # Формируем URL для запроса к deepseek-free-api (совместим с OpenAI)
    base_url = DEEPSEEK_API_URL.rstrip('/')
    url = f"{base_url}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": last_user_msg}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"DeepSeek API error: {resp.status} - {text}")
                raise Exception(f"DeepSeek API error: {resp.status}")
            data = await resp.json()
            # Ответ должен быть в формате OpenAI: choices[0].message.content
            return data["choices"][0]["message"]["content"]
