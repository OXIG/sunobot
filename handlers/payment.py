from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, Message
from aiogram import Bot
from config import PROVIDER_TOKEN

router = Router()

# --- Клавиатура с товарами ---
def get_products_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎵 1 генерация (50 ₽)", callback_data="buy_50")],
        [InlineKeyboardButton(text="🎶 3 генерации (150 ₽)", callback_data="buy_150")],
        [InlineKeyboardButton(text="🎤 5 генераций (250 ₽)", callback_data="buy_250")],
        [InlineKeyboardButton(text="🎧 10 генераций (500 ₽)", callback_data="buy_500")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Команда /pay (теперь будет работать!) ---
@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    await message.answer(
        "🛍 *Добро пожаловать в Suno Bot!*\n\n"
        "Выберите количество генераций, чтобы создать уникальные треки с помощью ИИ.\n\n"
        "🎵 *1 генерация* — 50 ₽\n"
        "🎶 *3 генерации* — 150 ₽\n"
        "🎤 *5 генераций* — 250 ₽\n"
        "🎧 *10 генераций* — 500 ₽",
        reply_markup=get_products_keyboard(),
        parse_mode="Markdown"
    )

# --- Команда /catalog (оставляем для удобства) ---
@router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    await cmd_pay(message)  # Просто вызываем ту же логику, что и для /pay

# --- Обработчик нажатия на кнопки товаров ---
@router.callback_query(lambda c: c.data and c.data.startswith("buy_"))
async def process_buy_callback(callback: types.CallbackQuery, bot: Bot):
    price_map = {
        "buy_50": (5000, "1 генерация музыки"),
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
        payload=f"balance_{callback.data}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        need_phone_number=True,
        need_email=True,
        send_phone_number_to_provider=True,
        send_email_to_provider=True,
    )
    await callback.answer()

# --- Обязательный обработчик предварительной проверки ---
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# --- Обработчик успешного платежа ---
@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    total_amount = message.successful_payment.total_amount // 100
    await message.answer(
        f"✅ Оплата на сумму {total_amount} ₽ успешно прошла!\n"
        f"Генерации скоро появятся на вашем балансе. Спасибо за покупку!"
    )
    # Здесь будет логика начисления генераций на баланс пользователя
