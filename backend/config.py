import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id_.strip()) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_.strip()]

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nanocoin.db")

# Backend API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Web App URL
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Game Constants
MAX_ENERGY = 1000
MAX_ELECTRICITY = 5000
BASE_CLICK_COINS = 1
ENERGY_REFILL_COST_DIAMONDS = 2
ENERGY_REFILL_AMOUNT = 50
BOOST_COST_DIAMONDS = 5
BOOST_DURATION_MINUTES = 15
BOOST_MULTIPLIER = 2
DIAMOND_DROP_CHANCE = 0.01  # 1%

# Mining
MIN_MINING_CLAIM_INTERVAL_MINUTES = 1

# Market
MARKET_TAX_PERCENT = 10

# Daily Rewards
DAILY_REWARDS_COINS = [100, 200, 500, 1000, 2000, 5000, 10000]
DAILY_REWARDS_DIAMONDS = [1, 2, 3, 5, 7, 10, 20]

# Experience
XP_PER_CLICK = 1
XP_PER_LEVEL_BASE = 100
XP_MULTIPLIER = 1.2

# Rate Limiting
RATE_LIMIT_CLICKS_PER_SECOND = 10
RATE_LIMIT_API_CALLS_PER_MINUTE = 60

# Strings (Farsi)
MSG_START = "به نانوکوین خوش آمدید! 🚀\nیک بازی مهیج برای استخراج و جمع‌آوری سکه و الماس."
MSG_REGISTERED = "شما با موفقیت ثبت‌نام شدید!"
MSG_ENERGY_EMPTY = "انرژی شما تمام شده است! ⚡️"
MSG_NOT_ENOUGH_DIAMONDS = "الماس کافی ندارید! 💎"
MSG_SHOP_WELCOME = "به فروشگاه خوش آمدید! چه چیزی میل دارید؟"
MSG_MARKET_WELCOME = "به بازار خوش آمدید! اینجا می‌توانید با دیگر بازیکنان معامله کنید."
