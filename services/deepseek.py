import aiohttp
import logging
from config import DEEPSEEK_API_URL

logger = logging.getLogger(__name__)

# Тот же токен, что и в переменной DEEP_SEEK_CHAT_AUTHORIZATION на Railway
DEEPSEEK_TOKEN = "w2SP85s/2KqbClBMCRncN25eootbMpy/XakRDkvNw5/qj9kjWJSNZ0VOPFgFN90G"

async def get_lyrics(messages_history: list) -> str:
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    if not DEEPSEEK_API_URL:
        raise Exception("DEEPSEEK_API_URL не задана в переменных окружения")

    base_url = DEEPSEEK_API_URL.rstrip('/')
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_TOKEN}"
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
            logger.info(f"Ответ от DeepSeek API (статус {resp.status}): {text[:500]}")
            if resp.status != 200:
                raise Exception(f"DeepSeek API error: {resp.status} - {text}")
            data = await resp.json()
            if "choices" not in data:
                logger.error(f"Неожиданный формат ответа: {data}")
                raise Exception(f"Ответ от DeepSeek не содержит 'choices': {data}")
            return data["choices"][0]["message"]["content"]
