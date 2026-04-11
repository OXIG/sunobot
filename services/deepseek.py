import aiohttp
import logging
from config import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

async def get_lyrics(messages_history: list) -> str:
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
            return data["choices"][0]["message"]["content"]
