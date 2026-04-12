import logging
from aiogram import Router, types
from aiogram.filters import Command
from database.crud import get_user_balance
from database.session import async_session_maker

logger = logging.getLogger(__name__)

router = Router()

# Простой тестовый обработчик
@router.message()
async def echo_all(message: types.Message):
    logger.info(f"Получено любое сообщение: {message.text}")
    await message.answer(f"Эхо: {message.text}")

@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"=== КОМАНДА BALANCE от {user_id} ===")
    
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
        logger.info(f"Баланс из БД: {balance}")
    
    await message.answer(f"💰 Ваш баланс: {balance} генераций")
