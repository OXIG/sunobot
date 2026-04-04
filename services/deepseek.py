import aiohttp
import json
from config import DEEPSEEK_API_KEY

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

async def get_lyrics(messages_history: list) -> str:
    """Отправляет историю сообщений в DeepSeek и возвращает текст песни."""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages_history,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"DeepSeek error: {resp.status} - {await resp.text()}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]