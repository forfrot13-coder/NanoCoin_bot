from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
from database.connection import get_session
from database.queries import get_user

async def casino_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🎰 اسلات", callback_data="casino_slots")],
        [InlineKeyboardButton("🚀 کرش (Crash)", callback_data="casino_crash")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    await query.edit_message_text(
        "به کازینو خوش آمدید! شانس خود را امتحان کنید. 🎰",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def casino_crash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    bet = 10 # 10 diamonds bet
    
    session = get_session()
    user = get_user(session, user_id)
    
    if user.diamonds < bet:
        await query.answer("الماس کافی ندارید! (۱۰ الماس نیاز است)", show_alert=True)
        session.close()
        return
        
    user.diamonds -= bet
    
    # Crash logic: random multiplier between 0 and 5
    multiplier = round(random.uniform(0, 5), 2)
    
    if multiplier < 1.0:
        msg = f"🚀 ضریب: `{multiplier}x`\n💥 متاسفانه باختید!"
    else:
        win = int(bet * multiplier)
        user.diamonds += win
        msg = f"🚀 ضریب: `{multiplier}x`\n💰 تبریک! شما برنده {win} الماس شدید!"
        
    session.commit()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="casino_main")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    session.close()

async def casino_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    cost = 5 # 5 diamonds per spin
    
    session = get_session()
    user = get_user(session, user_id)
    
    if user.diamonds < cost:
        await query.answer("الماس کافی ندارید! (۵ الماس نیاز است)", show_alert=True)
        session.close()
        return
        
    user.diamonds -= cost
    
    emojis = ["🍎", "💎", "🎰", "🔔", "🍒"]
    result = [random.choice(emojis) for _ in range(3)]
    
    msg = f"🎰 نتیجه: {' | '.join(result)}\n\n"
    
    if result[0] == result[1] == result[2]:
        win = 50
        user.diamonds += win
        msg += f"🎉 تبریک! شما برنده {win} الماس شدید!"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = 10
        user.diamonds += win
        msg += f"✨ خوب بود! شما برنده {win} الماس شدید!"
    else:
        msg += "😔 متاسفانه برنده نشدید. دوباره امتحان کنید!"
        
    session.commit()
    
    keyboard = [
        [InlineKeyboardButton("🎰 چرخش دوباره (۵ 💎)", callback_data="casino_slots")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="casino_main")]
    ]
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    session.close()
