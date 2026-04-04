# handlers/payment.py (продолжение)

from aiogram import Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message
from config import PROVIDER_TOKEN  # Токен мы добавим в config

# ... (предыдущий код с catalog и клавиатурой) ...

# Этот обработчик будет ловить нажатие на кнопки товаров
@router.callback_query(lambda c: c.data and c.data.startswith("buy_"))
async def process_buy_callback(callback: types.CallbackQuery, bot: Bot):
    # Определяем, что купили, по callback data
    price_map = {
        "buy_50": (5000, "1 генерация музыки"),   # 5000 копеек = 50 руб
        "buy_150": (15000, "3 генерации музыки"),
        "buy_250": (25000, "5 генераций музыки"),
        "buy_500": (50000, "10 генераций музыки"),
    }
    price_in_kopecks, description = price_map[callback.data]
    prices = [LabeledPrice(label="Пополнение баланса", amount=price_in_kopecks)]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Пополнение баланса",
        description=description,
        payload=f"balance_{callback.data}", # Уникальный идентификатор платежа
        provider_token=PROVIDER_TOKEN,      # Тот самый тестовый токен
        currency="RUB",
        prices=prices,
        need_phone_number=True,             # ЮKassa просит телефон для чека
        need_email=True,                    # И email
        send_phone_number_to_provider=True,
        send_email_to_provider=True,
    )
    await callback.answer() # Закрываем "часики" на кнопке

# Обязательный обработчик для проверки платежа перед списанием
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # Всегда отвечаем "ок", чтобы Telegram разрешил оплату
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обработчик успешного платежа
@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    # Здесь можно начислить пользователю генерации
    total_amount = message.successful_payment.total_amount // 100
    await message.answer(
        f"✅ Оплата на сумму {total_amount} ₽ успешно прошла!\n"
        f"Генерации скоро появятся на вашем балансе. Спасибо за покупку!"
    )
    # Вызовите здесь вашу функцию начисления баланса, например:
    # await add_generations_to_user(message.from_user.id, total_amount // 50)