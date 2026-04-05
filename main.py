import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.session import init_db
from handlers import start, balance, payment, generate, admin

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем все роутеры
dp.include_router(start.router)
dp.include_router(balance.router)
dp.include_router(payment.router)
dp.include_router(generate.router)
dp.include_router(admin.router)

# Запуск бота
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
