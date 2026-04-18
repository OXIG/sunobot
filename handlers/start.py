from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging

logger = logging.getLogger(__name__)

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
        [InlineKeyboardButton(text="🎵 Сгенерировать", callback_data="inline_generate")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="inline_balance")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data="inline_pay")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Команда /start от {message.from_user.id}")
    await message.answer(
        "🎵 Добро пожаловать в Suno Bot!\n\n"
        "Я помогу создать песню с помощью нейросети. Для генерации нужно пополнить баланс.\n\n"
        "Используйте кнопки ниже или под сообщением для навигации.",
        reply_markup=get_reply_keyboard()
    )
    await message.answer("Меню:", reply_markup=get_inline_keyboard())

@router.callback_query(lambda c: c.data == "inline_generate")
async def inline_generate(callback: CallbackQuery):
    logger.info(f"Нажата инлайн-кнопка inline_generate от {callback.from_user.id}")
    await callback.answer()
    await callback.message.answer("Введите /generate для создания песни")

@router.callback_query(lambda c: c.data == "inline_balance")
async def inline_balance(callback: CallbackQuery):
    logger.info(f"Нажата инлайн-кнопка inline_balance от {callback.from_user.id}")
    await callback.answer()
    await callback.message.answer("Введите /balance для проверки баланса")

@router.callback_query(lambda c: c.data == "inline_pay")
async def inline_pay(callback: CallbackQuery):
    logger.info(f"Нажата инлайн-кнопка inline_pay от {callback.from_user.id}")
    await callback.answer()
    await callback.message.answer("Введите /pay для пополнения баланса")

@router.callback_query(lambda c: c.data == "help")
async def inline_help(callback: CallbackQuery):
    logger.info(f"Нажата инлайн-кнопка help от {callback.from_user.id}")
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
