import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from config import BOT_TOKEN, YOOKASSA_RETURN_URL
from database.session import init_db
from handlers import start, balance, payment, generate, admin
from services.yookassa import Configuration
import yookassa

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(start.router)
dp.include_router(balance.router)
dp.include_router(payment.router)
dp.include_router(generate.router)
dp.include_router(admin.router)

# Вебхук для YooKassa
async def yookassa_webhook(request):
    from services.yookassa import check_payment
    from database.crud import update_payment_status, get_payment_by_id, add_balance
    from database.session import async_session_maker
    from services.mynalog import create_receipt

    data = await request.json()
    event = data.get('event')
    if event == 'payment.succeeded':
        payment_id = data['object']['id']
        payment_info = await check_payment(payment_id)
        if payment_info['status'] == 'succeeded':
            async with async_session_maker() as session:
                payment = await get_payment_by_id(session, payment_id)
                if payment and payment.status == 'pending':
                    # Добавляем баланс
                    user_id = payment.user_id
                    generations = payment.generations_added
                    await add_balance(session, user_id, generations)
                    await update_payment_status(session, payment_id, 'succeeded')
                    # Отправляем чек
                    await create_receipt("79991234567", payment.amount, "Пополнение баланса бота")
    return web.Response(status=200)

# Запуск бота
async def main():
    await init_db()
    # Запускаем веб-сервер для вебхуков YooKassa
    app = web.Application()
    app.router.add_post('/yookassa-webhook', yookassa_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    # Запускаем поллинг бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())