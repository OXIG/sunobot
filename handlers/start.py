from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

# Функция для создания главного меню (inline-клавиатуры)
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎵 СГЕНЕРИРОВАТЬ", callback_data="generate")],
        [InlineKeyboardButton(text="💰 БАЛАНС", callback_data="balance"),
         InlineKeyboardButton(text="💳 ПОПОЛНЕНИЕ", callback_data="pay")],
        [InlineKeyboardButton(text="❓ ПОМОЩЬ", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Хендлер команды /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 Добро пожаловать в Suno Bot!\n\n"
        "Я помогу создать песню с помощью нейросети. Для генерации нужно пополнить баланс.\n\n"
        "Используйте кнопки ниже для навигации.",
        reply_markup=get_main_keyboard()
    )

# Хендлер для нажатия на кнопку "СГЕНЕРИРОВАТЬ"
@router.callback_query(lambda c: c.data == "generate")
async def process_generate_callback(callback: CallbackQuery):
    await callback.answer() # Убираем "часики" на кнопке
    from .generate import start_generation
    # Вызываем вашу существующую функцию, передавая сообщение и state=None
    await start_generation(callback.message, None)

# Хендлер для кнопки "БАЛАНС"
@router.callback_query(lambda c: c.data == "balance")
async def process_balance_callback(callback: CallbackQuery):
    await callback.answer()
    from .balance import show_balance
    await show_balance(callback.message)

# Хендлер для кнопки "ПОПОЛНЕНИЕ"
@router.callback_query(lambda c: c.data == "pay")
async def process_pay_callback(callback: CallbackQuery):
    await callback.answer()
    from .payment import cmd_pay
    await cmd_pay(callback.message)

# Хендлер для кнопки "ПОМОЩЬ"
@router.callback_query(lambda c: c.data == "help")
async def process_help_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Доступные команды:\n"
        "/start — приветствие\n"
        "/generate — начать создание песни\n"
        "/balance — мой баланс\n"
        "/pay — пополнить баланс\n"
        "/catalog — магазин\n"
        "/help — эта справка"
    )
