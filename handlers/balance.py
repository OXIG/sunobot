import logging
from aiogram import Router, types
from aiogram.filters import Command
from database.crud import get_user_balance
from database.session import async_session_maker

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    await message.answer(f"💰 Ваш баланс: {balance} генераций")

@router.message(lambda msg: msg.text == "/balance 💰" or msg.text == "Мой баланс")
async def text_balance(message: types.Message):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        balance = await get_user_balance(session, user_id)
    await message.answer(f"💰 Ваш баланс: {balance} генераций")
