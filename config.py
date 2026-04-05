import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Suno API (прокси)
SUNO_API_URL = os.getenv("SUNO_API_URL", "http://localhost:3000")

# Telegram Payments (ЮKassa через BotFather)
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")   # <--- ЭТО ДОБАВЛЕНО

# YooKassa (если используете прямую интеграцию, но сейчас не нужно)
# YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
# YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
# YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL")

# Мой налог
MYNALOG_JWT_TOKEN = os.getenv("MYNALOG_JWT_TOKEN")
MYNALOG_INN = os.getenv("MYNALOG_INN")
MYNALOG_PHONE = os.getenv("MYNALOG_PHONE")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# Глобальный лимит генераций в месяц (в токенах Suno)
GLOBAL_LIMIT = int(os.getenv("GLOBAL_LIMIT", 200))
