from database.models import User, GameItem, Inventory
from config import XP_PER_LEVEL_BASE, XP_MULTIPLIER

def format_user_profile(user: User):
    xp_needed = int(XP_PER_LEVEL_BASE * (user.click_level ** XP_MULTIPLIER))
    
    text = (
        f"👤 *پروفایل کاربری: {user.first_name}*\n\n"
        f"💰 سکه: `{user.coins:,}`\n"
        f"💎 الماس: `{user.diamonds:,}`\n"
        f"⚡️ انرژی: `{user.energy}/{user.max_energy}`\n"
        f"🔌 برق: `{user.electricity}/{user.max_electricity}`\n\n"
        f"📈 سطح کلیک: `{user.click_level}`\n"
        f"✨ تجربه: `{user.click_xp}/{xp_needed}`\n"
        f"🔥 تقویت‌کننده: {'فعال' if user.active_boost_until else 'غیرفعال'}\n"
    )
    return text

def format_item_details(item: GameItem):
    text = (
        f"{item.emoji} *{item.name}*\n"
        f"📝 کد: `{item.item_code}`\n"
        f"💰 قیمت: `{item.price_diamonds} 💎`\n"
    )
    
    if item.mining_rate > 0:
        text += f"⛏ استخراج: `{item.mining_rate} سکه در ساعت`\n"
    if item.electricity_consumption > 0:
        text += f"🔌 مصرف برق: `{item.electricity_consumption} در ساعت`\n"
    if item.buff_click_coins > 0:
        text += f"🖱 پاداش کلیک: `+{item.buff_click_coins}`\n"
        
    return text

def format_inventory(inventory_list):
    if not inventory_list:
        return "کوله پشتی شما خالی است! 🎒"
    
    text = "🎒 *کوله پشتی شما:*\n\n"
    for inv in inventory_list:
        status = "✅" if inv.is_active else "❌"
        text += f"{inv.item.emoji} {inv.item.name} (تعداد: {inv.quantity}) {status if inv.item.item_type.value == 'MINER' else ''}\n"
    
    return text

def format_leaderboard(users):
    text = "🏆 *برترین بازیکنان:*\n\n"
    for i, user in enumerate(users, 1):
        text += f"{i}. {user.first_name} - `{user.coins:,} سکه`\n"
    return text
