import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, Message
from aiogram import Bot
from config import PROVIDER_TOKEN
from database.crud import add_balance, get_or_create_user
from database.session import async_session_maker

logger = logging.getLogger(__name__)

router = Router()

def get_products_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎵 1 генерация (80 ₽)", callback_data="buy_80")],
        [InlineKeyboardButton(text="🎶 3 генерации (240 ₽)", callback_data="buy_240")],
        [InlineKeyboardButton(text="🎤 5 генераций (400 ₽)", callback_data="buy_400")],
        [InlineKeyboardButton(text="🎧 10 генераций (800 ₽)", callback_data="buy_800")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    await message.answer(
        "🛍 *Добро пожаловать в Suno Bot!*\n\n"
        "Выберите количество генераций, чтобы создать уникальные треки с помощью ИИ.\n\n"
        "🎵 *1 генерация* — 80 ₽\n"
        "🎶 *3 генерации* — 240 ₽\n"
        "🎤 *5 генераций* — 400 ₽\n"
        "🎧 *10 генераций* — 800 ₽",
        reply_markup=get_products_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    await cmd_pay(message)

@router.callback_query(lambda c: c.data and c.data.startswith("buy_"))
async def process_buy_callback(callback: types.CallbackQuery, bot: Bot):
    logger.info(f"Получен callback: {callback.data}")
    
    if not PROVIDER_TOKEN:
        logger.error("PROVIDER_TOKEN не задан в переменных окружения!")
        await callback.message.answer("❌ Ошибка: платежный токен не настроен. Сообщите администратору.")
        await callback.answer()
        return

    price_map = {
        "buy_80": (8000, "1 генерация музыки"),
        "buy_240": (24000, "3 генерации музыки"),
        "buy_400": (40000, "5 генераций музыки"),
        "buy_800": (80000, "10 генераций музыки"),
    }
    price_in_kopecks, description = price_map[callback.data]
    prices = [LabeledPrice(label="Пополнение баланса", amount=price_in_kopecks)]

    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Пополнение баланса",
            description=description,
            payload=f"balance_{callback.data}",
            provider_token=PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            need_phone_number=True,
            need_email=True,
            send_phone_number_to_provider=True,
            send_email_to_provider=True,
        )
    except Exception as e:
        logger.exception("Ошибка при отправке инвойса")
        await callback.message.answer(f"❌ Ошибка при создании счета: {str(e)}")
    
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    total_amount = message.successful_payment.total_amount // 100  # рубли
    # Определяем количество генераций по сумме
    generations_map = {80: 1, 240: 3, 400: 5, 800: 10}
    generations = generations_map.get(total_amount, 0)
    if generations == 0:
        await message.answer("❌ Неизвестная сумма платежа. Свяжитесь с поддержкой.")
        return

    # Начисляем генерации пользователю
    async with async_session_maker() as session:
        user = await get_or_create_user(session, message.from_user.id)
        await add_balance(session, message.from_user.id, generations)
        new_balance = await get_user_balance(session, message.from_user.id)  # нужно импортировать get_user_balance, или можно просто вернуть сообщение

    # Импортируем get_user_balance, чтобы показать новый баланс (либо оставим без показа)
    from database.crud import get_user_balance
    async with async_session_maker() as session:
        new_balance = await get_user_balance(session, message.from_user.id)

    await message.answer(
        f"✅ Оплата на сумму {total_amount} ₽ успешно прошла!\n"
        f"Вам начислено {generations} генераций.\n"
        f"💰 Ваш баланс: {new_balance} генераций.\n"
        f"Спасибо за покупку!"
    )
