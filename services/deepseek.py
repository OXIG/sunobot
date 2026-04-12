import aiohttp
import logging
from config import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """Ты — ассистент для написания текстов песен для нейросети Suno.

ПРАВИЛА:
1. Отвечай ТОЛЬКО по делу. Без воды, без лишних объяснений.
2. Твои ответы должны быть краткими (максимум 2-3 предложения).
3. Если пользователь просит текст песни — сразу пиши текст в формате:
   [КУПЛЕТ 1]
   [ПРИПЕВ]
   [КУПЛЕТ 2]
   [ПРИПЕВ]
   [БРИДЖ]
   [КУПЛЕТ 3]
   [ПРИПЕВ]
4. По умолчанию текст = 3 куплета + бридж + припев.
5. Не задавай лишних вопросов.
6. В конце каждого готового текста добавь строку: [ТЕКСТ_ГОТОВ]
7. Если пользователь просит указать стиль — подбирай 4-5 слов (pop, rock, hip-hop, electronic, lo-fi, orchestral, ambient)."""

async def get_lyrics(messages_history: list) -> str:
    # Добавляем системный промпт, если его нет
    if not messages_history or messages_history[0].get("role") != "system":
        messages_history.insert(0, {"role": "system", "content": DEFAULT_SYSTEM_PROMPT})
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages_history,
        "temperature": 0.7,
        "max_tokens": 1500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"DeepSeek API error: {resp.status} - {text}")
                raise Exception(f"DeepSeek API error: {resp.status}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
