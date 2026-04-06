import aiohttp
import logging
from config import DEEPSEEK_API_URL

logger = logging.getLogger(__name__)

# Токен уже передан в deepseek-free-api через переменную окружения,
# поэтому в запросе мы его не указываем? НЕТ: deepseek-free-api требует заголовок Authorization
# Используем тот же токен, что и в Railway
DEEPSEEK_TOKEN = "oDxN0DC4os28SAct1ViIuHtGJSpkkPryQoiZ0vsJAvjXtwDM3rhhlex3svlAqPjp"

async def get_lyrics(messages_history: list) -> str:
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    if not DEEPSEEK_API_URL:
        raise Exception("DEEPSEEK_API_URL не задана")

    base_url = DEEPSEEK_API_URL.rstrip('/')
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": DEEPSEEK_TOKEN   # без "Bearer"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": last_user_msg}],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            text = await resp.text()
            logger.info(f"Ответ DeepSeek (статус {resp.status}): {text[:500]}")
            if resp.status != 200:
                raise Exception(f"DeepSeek error: {resp.status} - {text}")
            data = await resp.json()
            if "choices" not in data:
                raise Exception(f"Неожиданный ответ: {data}")
            return data["choices"][0]["message"]["content"]
