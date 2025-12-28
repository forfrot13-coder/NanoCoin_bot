import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id_.strip()) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_.strip()]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nanocoin.db")

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

# Strings (Farsi)
MSG_START = "به نانوکوین خوش آمدید! 🚀\nیک بازی مهیج برای استخراج و جمع‌آوری سکه و الماس."
MSG_REGISTERED = "شما با موفقیت ثبت‌نام شدید!"
MSG_ENERGY_EMPTY = "انرژی شما تمام شده است! ⚡️"
MSG_NOT_ENOUGH_DIAMONDS = "الماس کافی ندارید! 💎"
MSG_SHOP_WELCOME = "به فروشگاه خوش آمدید! چه چیزی میل دارید؟"
MSG_MARKET_WELCOME = "به بازار خوش آمدید! اینجا می‌توانید با دیگر بازیکنان معامله کنید."
