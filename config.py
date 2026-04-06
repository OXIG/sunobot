import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")   # не используется, но пусть будет
SUNO_API_URL = os.getenv("SUNO_API_URL", "http://localhost:3000")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "http://localhost:3001")
MYNALOG_JWT_TOKEN = os.getenv("MYNALOG_JWT_TOKEN")
MYNALOG_INN = os.getenv("MYNALOG_INN")
MYNALOG_PHONE = os.getenv("MYNALOG_PHONE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
GLOBAL_LIMIT = int(os.getenv("GLOBAL_LIMIT", 200))

# Новый ключ для OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
