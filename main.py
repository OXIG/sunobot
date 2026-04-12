import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from database.crud import create_payment, get_or_create_user
from database.session import async_session_maker
from services.yookassa import create_yookassa_payment

logger = logging.getLogger(__name__)

router = Router()

def get_products_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎵 1 генерация (50 ₽)", callback_data="buy_50")],
        [InlineKeyboardButton(text="🎶 3 генерации (150 ₽)", callback_data="buy_150")],
        [InlineKeyboardButton(text="🎤 5 генераций (250 ₽)", callback_data="buy_250")],
        [InlineKeyboardButton(text="🎧 10 генераций (500 ₽)", callback_data="buy_500")],
        [InlineKeyboardButton(text="⭐ 20 генераций (1000 ₽)", callback_data="buy_1000")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    await message.answer(
        "🛍 *Добро пожаловать в Suno Bot!*\n\n"
        "Выберите количество генераций, чтобы создать уникальные треки с помощью ИИ.\n\n"
        "🎵 *1 генерация* — 50 ₽\n"
        "🎶 *3 генерации* — 150 ₽\n"
        "🎤 *5 генераций* — 250 ₽\n"
        "🎧 *10 генераций* — 500 ₽\n"
        "⭐ *20 генераций* — 1000 ₽\n\n"
        "💳 *Оплата через ЮKassa* (банковские карты, СБП, Apple Pay)",
        reply_markup=get_products_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(lambda c: c.data and c.data.startswith("buy_"))
async def process_buy_callback(callback: types.CallbackQuery):
    logger.info(f"Получен callback: {callback.data}")
    
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        logger.error("YooKassa credentials not configured!")
        await callback.message.answer("❌ Ошибка: платежная система не настроена. Сообщите администратору.")
        await callback.answer()
        return

    price_map = {
        "buy_50": (50, 1, "1 генерация музыки"),
        "buy_150": (150, 3, "3 генерации музыки"),
        "buy_250": (250, 5, "5 генераций музыки"),
        "buy_500": (500, 10, "10 генераций музыки"),
        "buy_1000": (1000, 20, "20 генераций музыки"),
    }
    
    amount, generations, description = price_map[callback.data]
    
    async with async_session_maker() as session:
        user = await get_or_create_user(session, callback.from_user.id)
        
        # Создаём платёж в базе
        payment = await create_payment(session, user.id, amount, f"payment_{callback.from_user.id}_{int(asyncio.get_event_loop().time())}")
        
        # Создаём платёж в YooKassa
        payment_id, payment_url = await create_yookassa_payment(
            amount=amount,
            description=description,
            user_id=callback.from_user.id,
            payment_id=payment.id
        )
        
        # Обновляем yookassa_payment_id в базе
        payment.yookassa_payment_id = payment_id
        await session.commit()
    
    # Создаём клавиатуру с кнопкой оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ОПЛАТИТЬ", url=payment_url)],
        [InlineKeyboardButton(text="🏠 На главную", callback_data="main_menu")]
    ])
    
    await callback.message.answer(
        f"💳 *Счёт на оплату*\n\n"
        f"💰 Сумма: {amount} ₽\n"
        f"🎵 Генераций: {generations}\n\n"
        f"Нажмите на кнопку ниже, чтобы оплатить.\n"
        f"После оплаты баланс пополнится автоматически.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
