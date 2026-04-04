from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.request.payment_request import PaymentRequest
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, YOOKASSA_RETURN_URL

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

async def create_payment(amount: float, user_id: int, description: str = "Пополнение баланса") -> tuple[str, str]:
    """
    Создаёт платёж в YooKassa.
    Возвращает (payment_id, confirmation_url).
    """
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
        "description": description,
        "metadata": {
            "user_id": str(user_id)
        }
    })
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