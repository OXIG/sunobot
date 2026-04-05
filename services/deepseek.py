import aiohttp
import logging

logger = logging.getLogger(__name__)

DEEPSEEK_TOKEN = "w2SP85s/2KqbClBMCRncN25eootbMpy/XakRDkvNw5/qj9kjWJSNZ0VOPFgFN90G"

async def get_lyrics(messages_history: list) -> str:
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break
    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    # Пробуем другой эндпоинт (официальный API)
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_TOKEN}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": last_user_msg}],
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            text = await resp.text()
            if resp.status != 200:
                logger.error(f"DeepSeek API error: {resp.status} - {text}")
                raise Exception(f"DeepSeek API error: {resp.status} - {text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
