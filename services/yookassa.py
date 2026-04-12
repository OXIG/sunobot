import uuid
from yookassa import Configuration, Payment as YooPayment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, YOOKASSA_RETURN_URL

# Настройка YooKassa
Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

async def create_yookassa_payment(amount: float, description: str, user_id: int, payment_id: int) -> tuple[str, str]:
    """
    Создаёт платёж в YooKassa.
    Возвращает (payment_id, confirmation_url).
    """
    idempotence_key = str(uuid.uuid4())
    
    payment = YooPayment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": YOOKASSA_RETURN_URL
        },
        "capture": True,
        "description": f"{description} (пользователь {user_id})",
        "metadata": {
            "user_id": str(user_id),
            "payment_id": str(payment_id)
        }
    }, idempotence_key)
    
    return payment.id, payment.confirmation.confirmation_url

async def check_payment(payment_id: str) -> dict:
    """
    Проверяет статус платежа.
    Возвращает словарь с информацией.
    """
    payment = YooPayment.find_one(payment_id)
    return {
        "status": payment.status,
        "amount": float(payment.amount.value),
        "metadata": payment.metadata
    }
