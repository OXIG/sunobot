import aiohttp
from config import DEEPSEEK_API_URL

DEEPSEEK_URL = DEEPSEEK_API_URL.rstrip('/') + '/v1/chat/completions'

async def get_lyrics(messages_history: list) -> str:
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": messages_history,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"DeepSeek error: {resp.status} - {text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
