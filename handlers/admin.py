from aiogram import Router, types
from aiogram.filters import Command
from database.crud import get_current_month_counter
from database.session import async_session_maker
from config import GLOBAL_LIMIT

router = Router()

@router.message(Command("admin_stats"))
async def admin_stats(message: types.Message):
    # Проверка, что пользователь админ (можно по ID)
    if message.from_user.id != 123456789:  # замените на ваш ID
        return
    async with async_session_maker() as session:
        count = await get_current_month_counter(session)
    await message.answer(f"📊 Глобальный счётчик: {count}/{GLOBAL_LIMIT}")