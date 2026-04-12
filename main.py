import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.session import init_db
from handlers import start, balance, payment, generate, admin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры СНАЧАЛА
dp.include_router(start.router)
dp.include_router(balance.router)
dp.include_router(payment.router)
dp.include_router(generate.router)
dp.include_router(admin.router)

# ВРЕМЕННЫЙ ТЕСТОВЫЙ ОБРАБОТЧИК - В КОНЦЕ (как fallback)
@dp.message()
async def catch_all(message: types.Message):
    logging.info(f"🔵 Fallback: сообщение не обработано: {message.text} от {message.from_user.id}")
    await message.answer(f"🔵 Команда не распознана. Используйте /start")

async def main():
    await init_db()
    print("✅ Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
