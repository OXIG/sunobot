from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="🎵 СГЕНЕРИРОВАТЬ")],
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

@router.message(lambda msg: msg.text == "🎵 СГЕНЕРИРОВАТЬ")
async def generate_button(message: types.Message):
    from .generate import start_generation
    # start_generation ожидает два аргумента: message и state.
    # Передаём state=None, т.к. это начало нового диалога.
    await start_generation(message, None)

@router.message(lambda msg: msg.text == "💰 БАЛАНС")
async def balance_button(message: types.Message):
    from .balance import show_balance
    await show_balance(message)

@router.message(lambda msg: msg.text == "💳 ПОПОЛНЕНИЕ")
async def pay_button(message: types.Message):
    from .payment import cmd_pay
    await cmd_pay(message)

@router.message(lambda msg: msg.text == "❓ ПОМОЩЬ")
async def help_button(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — приветствие\n"
        "/generate — начать создание песни\n"
        "/balance — мой баланс\n"
        "/pay — пополнить баланс\n"
        "/catalog — магазин\n"
        "/help — эта справка"
    )
