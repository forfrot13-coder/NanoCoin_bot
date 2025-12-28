from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🖱 کلیک", callback_data="game_click"), InlineKeyboardButton("⛏ استخراج", callback_data="game_mine")],
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop_main"), InlineKeyboardButton("⚖️ بازار", callback_data="market_main")],
        [InlineKeyboardButton("🎰 کازینو", callback_data="casino_main"), InlineKeyboardButton("👤 پروفایل", callback_data="profile_main")],
        [InlineKeyboardButton("🎯 ماموریت‌ها", callback_data="quests_main"), InlineKeyboardButton("🏆 دستاوردها", callback_data="achievements_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def shop_keyboard(items):
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(f"{item.emoji} {item.name} - {item.price_diamonds}💎", callback_data=f"shop_buy_{item.id}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎒 کوله پشتی", callback_data="inventory_main")],
        [InlineKeyboardButton("📈 برترین‌ها", callback_data="leaderboard_main")],
        [InlineKeyboardButton("🔥 خرید تقویت‌کننده", callback_data="buy_boost")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data="main_menu")]])
