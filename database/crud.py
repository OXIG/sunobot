from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from .models import User, Generation, Payment, GlobalCounter
from config import GLOBAL_LIMIT

# User
async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
    return user

async def get_user_balance(session: AsyncSession, telegram_id: int) -> int:
    user = await get_or_create_user(session, telegram_id)
    return user.balance

async def add_balance(session: AsyncSession, telegram_id: int, generations: int):
    user = await get_or_create_user(session, telegram_id)
    user.balance += generations
    await session.commit()

async def deduct_balance(session: AsyncSession, telegram_id: int, generations: int = 1) -> bool:
    user = await get_or_create_user(session, telegram_id)
    if user.balance >= generations:
        user.balance -= generations
        await session.commit()
        return True
    return False

# Generation
async def save_generation(session: AsyncSession, user_id: int, prompt_text: str, style: str, vocal_type: str, audio_url1: str, audio_url2: str):
    gen = Generation(
        user_id=user_id,
        prompt_text=prompt_text,
        style=style,
        vocal_type=vocal_type,
        audio_url1=audio_url1,
        audio_url2=audio_url2
    )
    session.add(gen)
    await session.commit()

# Payment
async def create_payment(session: AsyncSession, user_id: int, amount: float, yookassa_payment_id: str) -> Payment:
    generations = int(amount / 50)  # 50 руб = 1 генерация
    payment = Payment(
        user_id=user_id,
        amount=amount,
        generations_added=generations,
        yookassa_payment_id=yookassa_payment_id,
        status="pending"
    )
    session.add(payment)
    await session.commit()
    return payment

async def update_payment_status(session: AsyncSession, yookassa_payment_id: str, status: str):
    stmt = update(Payment).where(Payment.yookassa_payment_id == yookassa_payment_id).values(status=status)
    await session.execute(stmt)
    await session.commit()

async def get_payment_by_id(session: AsyncSession, yookassa_payment_id: str) -> Payment:
    result = await session.execute(select(Payment).where(Payment.yookassa_payment_id == yookassa_payment_id))
    return result.scalar_one_or_none()

# Global counter
async def get_current_month_counter(session: AsyncSession) -> int:
    now = datetime.now()
    result = await session.execute(
        select(GlobalCounter).where(
            and_(GlobalCounter.year == now.year, GlobalCounter.month == now.month)
        )
    )
    counter = result.scalar_one_or_none()
    if not counter:
        counter = GlobalCounter(year=now.year, month=now.month, count=0)
        session.add(counter)
        await session.commit()
    return counter.count

async def increment_global_counter(session: AsyncSession) -> bool:
    now = datetime.now()
    result = await session.execute(
        select(GlobalCounter).where(
            and_(GlobalCounter.year == now.year, GlobalCounter.month == now.month)
        )
    )
    counter = result.scalar_one_or_none()
    if not counter:
        counter = GlobalCounter(year=now.year, month=now.month, count=0)
        session.add(counter)
    if counter.count >= GLOBAL_LIMIT:
        return False
    counter.count += 1
    await session.commit()
    return True