from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 Добро пожаловать в Suno Bot!\n\n"
        "Я помогу создать песню с помощью нейросети. Для генерации нужно пополнить баланс.\n\n"
        "Команды:\n"
        "/generate — начать создание песни\n"
        "/balance — мой баланс\n"
        "/pay — пополнить баланс\n"
        "/help — помощь"
    )
