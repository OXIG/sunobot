from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Reply-кнопки (внизу экрана)
def get_reply_keyboard():
    buttons = [
        [KeyboardButton(text="/generate 🎵")],
        [KeyboardButton(text="/balance 💰"), KeyboardButton(text="/pay 💳")],
        [KeyboardButton(text="/help ❓")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Inline-кнопки (под сообщением)
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
        reply_markup=get_reply_keyboard()       # Reply-кнопки
    )
    # Дополнительно отправляем сообщение с Inline-кнопками
    await message.answer(
        "А также можете использовать инлайн-кнопки:",
        reply_markup=get_inline_keyboard()
    )
