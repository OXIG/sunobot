from database.crud import get_current_month_counter, increment_global_counter
from database.session import async_session_maker
from config import GLOBAL_LIMIT

async def can_generate() -> bool:
    async with async_session_maker() as session:
        count = await get_current_month_counter(session)
        return count < GLOBAL_LIMIT

async def use_generation() -> bool:
    async with async_session_maker() as session:
        return await increment_global_counter(session)