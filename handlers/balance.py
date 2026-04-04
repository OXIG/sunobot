from aiogram import Router, types
from database.crud import get_user_balance
from database.session import async_session_maker

router = Router()

@router.message(lambda msg: msg.text == "/balance" or msg.text == "Мой баланс")
async def show_balance(message: types.Message):
    async with async_session_maker() as session:
        balance = await get_user_balance(session, message.from_user.id)
    await message.answer(f"💰 Ваш баланс: {balance} генераций")