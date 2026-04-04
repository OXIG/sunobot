import aiohttp
from loguru import logger
from config import MYNALOG_JWT_TOKEN, MYNALOG_INN, MYNALOG_PHONE

MYNALOG_API_URL = "https://lknpd.nalog.ru/api/v1/income"

async def create_receipt(user_phone: str, amount: float, description: str = "Пополнение баланса"):
    """
    Отправляет чек в Мой налог.
    user_phone - телефон пользователя (или ваш, если не знаем телефон клиента).
    """
    headers = {
        "Authorization": f"Bearer {MYNALOG_JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "operation": "Приход",
        "amount": amount,
        "description": description,
        "payment_type": "ELECTRONIC",
        "inn": MYNALOG_INN,
        "client_phone": user_phone  # или MYNALOG_PHONE, если не хотим запрашивать у пользователя
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(MYNALOG_API_URL, headers=headers, json=payload) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                logger.error(f"Ошибка отправки чека: {resp.status} {text}")
                return False
            return True