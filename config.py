import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SUNO_API_URL = os.getenv("SUNO_API_URL", "http://localhost:3000")

# YooKassa (основной способ оплаты)
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL", "https://t.me/YourBot")

# Telegram Payments (резервный или тестовый)
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

MYNALOG_JWT_TOKEN = os.getenv("MYNALOG_JWT_TOKEN")
MYNALOG_INN = os.getenv("MYNALOG_INN")
MYNALOG_PHONE = os.getenv("MYNALOG_PHONE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
GLOBAL_LIMIT = int(os.getenv("GLOBAL_LIMIT", 200))

# Админы
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]
