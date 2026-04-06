from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="🎵 СГЕНЕРИРОВАТЬ ")],
        [KeyboardButton(text="💰 БАЛАНС"), KeyboardButton(text="💳 ПОПОЛНЕНИЕ")],
        [KeyboardButton(text="❓ ПОМОЩЬ")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 Добро пожаловать в Suno Bot!\n\n"
        "Я помогу создать песню с помощью нейросети. Для генерации нужно пополнить баланс.\n\n"
        "Используйте кнопки ниже для навигации.",
        reply_markup=get_main_keyboard()
    )
