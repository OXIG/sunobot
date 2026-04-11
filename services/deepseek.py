import aiohttp
import logging
from config import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

# Системный промпт, который задаёт роль DeepSeek как голосового помощника для написания песен
SYSTEM_PROMPT = (
    "Ты — голосовой помощник для написания песен. "
    "Помоги пользователю написать текст песни на русском языке. "
    "Твоя задача — предложить тему, жанр, структуру (куплеты, припев) и помочь с рифмами. "
    "Будь креативным и дружелюбным. Отвечай на русском языке."
)

async def get_lyrics(messages_history: list) -> str:
    # Добавляем системный промпт в начало истории, если его ещё нет
    if not messages_history or messages_history[0].get("role") != "system":
        messages_history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    
    # Извлекаем последнее сообщение пользователя
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages_history,
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
            return data["choices"][0]["message"]["content"]
