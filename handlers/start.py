from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram import Bot, Dispatcher
    from config import BOT_TOKEN
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    state = FSMContext(storage=storage, chat_id=callback.from_user.id, user_id=callback.from_user.id)
    
    # Создаём новое сообщение
    new_message = await callback.message.answer("/generate")
    await start_generation(new_message, state)

@router.callback_query(lambda c: c.data == "balance")
async def inline_balance(callback: CallbackQuery):
    await callback.answer()
    from .balance import cmd_balance
    from config import BOT_TOKEN
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN)
    new_message = await callback.message.answer("/balance")
    await cmd_balance(new_message)

@router.callback_query(lambda c: c.data == "pay")
async def inline_pay(callback: CallbackQuery):
    await callback.answer()
    from .payment import cmd_pay
    from config import BOT_TOKEN
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN)
    new_message = await callback.message.answer("/pay")
    await cmd_pay(new_message)

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
