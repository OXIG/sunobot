import aiohttp
import asyncio
from typing import Optional, Tuple, Dict, Any
from loguru import logger
from config import SUNO_API_URL  # добавим эту переменную в .env

class SunoClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Универсальный метод для запросов к suno-api"""
        url = f"{self.base_url}{endpoint}"
        if self.session is None:
            self.session = aiohttp.ClientSession()
        async with self.session.request(method, url, **kwargs) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"Suno API error {resp.status}: {text}")
                raise Exception(f"Suno API error: {resp.status}")
            return await resp.json()

    async def generate(self, lyrics: str, style: str, vocal_type: str = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Генерирует два трека через suno-api.
        lyrics — текст песни (полный)
        style — жанр + опционально вокал (например, "pop, male vocal")
        """
        # Собираем tags: жанр + вокал, если указан
        tags = style
        if vocal_type and vocal_type.lower() in ["male", "female"]:
            tags = f"{style}, {vocal_type} vocal"

        payload = {
            "prompt": lyrics,
            "tags": tags,
            "title": "NeuralMusic Track",   # можно генерировать автоматически
            "make_instrumental": False,
            "wait_audio": False
        }

        # 1. Запускаем генерацию
        try:
            result = await self._request("POST", "/api/custom_generate", json=payload)
            # Ответ должен содержать список из двух объектов с полем id
            if not isinstance(result, list) or len(result) < 2:
                logger.error(f"Unexpected generate response: {result}")
                return None, None
            ids = [item["id"] for item in result[:2]]
        except Exception as e:
            logger.exception("Failed to start generation")
            return None, None

        # 2. Опрашиваем статус
        for _ in range(60):  # максимум 5 минут (60 * 5 сек)
            await asyncio.sleep(5)
            try:
                info = await self._request("GET", f"/api/get?ids={','.join(ids)}")
                if not isinstance(info, list) or len(info) < 2:
                    continue
                # Статус 'streaming' означает, что аудио готово
                if info[0].get("status") == "streaming" and info[1].get("status") == "streaming":
                    url1 = info[0].get("audio_url")
                    url2 = info[1].get("audio_url")
                    if url1 and url2:
                        return url1, url2
            except Exception:
                continue

        logger.error("Timeout or generation failed")
        return None, None

    async def get_limits(self) -> Dict:
        """Получить оставшиеся лимиты (токены)"""
        return await self._request("GET", "/api/get_limit")

    async def close(self):
        if self.session:
            await self.session.close()