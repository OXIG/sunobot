import aiohttp
import logging

logger = logging.getLogger(__name__)

# Ваш токен DeepSeek (полученный из браузера)
DEEPSEEK_TOKEN = "w2SP85s/2KqbClBMCRncN25eootbMpy/XakRDkvNw5/qj9kjWJSNZ0VOPFgFN90G"

async def get_lyrics(messages_history: list) -> str:
    """
    Отправляет историю сообщений в DeepSeek и возвращает текст ответа.
    """
    # Извлекаем последнее сообщение пользователя
    last_user_msg = None
    for msg in reversed(messages_history):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content")
            break

    if not last_user_msg:
        raise Exception("Не найдено сообщение пользователя в истории")

    url = "https://chat.deepseek.com/api/v0/chat/completion"
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
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"DeepSeek API error: {resp.status} - {text}")
                raise Exception(f"DeepSeek API error: {resp.status}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
