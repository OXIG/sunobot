from aiogram import Router, types
from aiogram.filters import Command
from database.crud import get_current_month_counter
from database.session import async_session_maker
from config import GLOBAL_LIMIT, ADMIN_IDS

router = Router()

@router.message(Command("admin_stats"))
async def admin_stats(message: types.Message):
    # Проверка, что пользователь админ
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    async with async_session_maker() as session:
        count = await get_current_month_counter(session)
    
    await message.answer(f"📊 Глобальный счётчик: {count}/{GLOBAL_LIMIT}")


@router.message(Command("add_balance"))
async def add_balance_command(message: types.Message):
    """Админская команда: /add_balance 123456789 10"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Использование: /add_balance <telegram_id> <количество_генераций>")
        return
    
    try:
        telegram_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ ID и количество должны быть числами.")
        return
    
    from database.crud import add_balance, get_or_create_user
    from database.session import async_session_maker
    
    async with async_session_maker() as session:
        await get_or_create_user(session, telegram_id)
        await add_balance(session, telegram_id, amount)
        new_balance = await get_user_balance(session, telegram_id)
    
    await message.answer(f"✅ Пользователю {telegram_id} добавлено {amount} генераций. Новый баланс: {new_balance}")


@router.message(Command("bot_stats"))
async def bot_stats(message: types.Message):
    """Админская команда: статистика бота"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    from database.crud import get_total_users, get_total_generations, get_total_payments
    from database.session import async_session_maker
    
    async with async_session_maker() as session:
        total_users = await get_total_users(session)
        total_generations = await get_total_generations(session)
        total_payments = await get_total_payments(session)
        monthly_count = await get_current_month_counter(session)
    
    await message.answer(
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🎵 Всего генераций: {total_generations}\n"
        f"💳 Всего платежей: {total_payments}\n"
        f"📅 Генераций в этом месяце: {monthly_count}/{GLOBAL_LIMIT}",
        parse_mode="Markdown"
    )
