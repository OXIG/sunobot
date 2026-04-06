from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

router = Router()

def get_reply_keyboard():
    buttons = [
        [KeyboardButton(text="/generate 🎵")],
        [KeyboardButton(text="/balance 💰"), KeyboardButton(text="/pay 💳")],
        [KeyboardButton(text="/help ❓")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_inline_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎵 Сгенерировать", callback_data="generate")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data="pay")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 Добро пожаловать в Suno Bot!\n\n"
        "Я помогу создать песню с помощью нейросети. Для генерации нужно пополнить баланс.\n\n"
        "Используйте кнопки ниже или под сообщением для навигации.",
        reply_markup=get_reply_keyboard()
    )
    await message.answer("Меню:", reply_markup=get_inline_keyboard())

@router.callback_query(lambda c: c.data == "generate")
async def inline_generate(callback: CallbackQuery):
    await callback.answer()
    from .generate import start_generation
    # Создаём фиктивное сообщение от имени пользователя
    fake_message = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user,
        text="/generate"
    )
    await start_generation(fake_message, None)

@router.callback_query(lambda c: c.data == "balance")
async def inline_balance(callback: CallbackQuery):
    await callback.answer()
    from .balance import show_balance
    await show_balance(callback.message)

@router.callback_query(lambda c: c.data == "pay")
async def inline_pay(callback: CallbackQuery):
    await callback.answer()
    from .payment import cmd_pay
    await cmd_pay(callback.message)

@router.callback_query(lambda c: c.data == "help")
async def inline_help(callback: CallbackQuery):
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
