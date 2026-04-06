import aiohttp
import logging
from config import OPENROUTER_API_KEY

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

    # Используем бесплатную модель через OpenRouter
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",  # бесплатная, мощная
        "messages": [{"role": "user", "content": last_user_msg}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            text = await resp.text()
            logger.info(f"OpenRouter ответ (статус {resp.status}): {text[:500]}")
            if resp.status != 200:
                raise Exception(f"OpenRouter error: {resp.status} - {text}")
            data = await resp.json()
            if "choices" not in data:
                raise Exception(f"Неожиданный ответ: {data}")
            return data["choices"][0]["message"]["content"]
