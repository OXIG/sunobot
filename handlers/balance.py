from aiogram import Router, types
from database.crud import get_user_balance
from database.session import async_session_maker
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(lambda msg: msg.text == "/balance" or msg.text == "Мой баланс")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Запрос баланса от пользователя {user_id}")
    
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    
    logger.info(f"Баланс пользователя {user_id}: {balance} генераций")
    await message.answer(f"💰 Ваш баланс: {balance} генераций")
