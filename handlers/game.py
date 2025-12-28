from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user, update_quest_progress, get_user_inventory
from utils.game_logic import process_click, calculate_mining_rewards
from utils.keyboards import main_menu_keyboard, back_to_main_keyboard
from datetime import datetime

async def click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    user = get_user(session, user_id)
    
    result, error = process_click(user, session)
    
    if error:
        await query.answer(error, show_alert=True)
        session.close()
        return

    session.commit()
    
    msg = f"🖱 کلیک موفق! +{result['coins_earned']} سکه"
    if result['leveled_up']:
        msg += "\n🆙 تبریک! شما به سطح جدیدی رسیدید!"
    if result['diamond_found']:
        msg += "\n💎 ایول! ۱ الماس پیدا کردید!"
        
    await query.answer(msg)
    
    # Update UI
    from utils.formatters import format_user_profile
    await query.edit_message_text(
        format_user_profile(user),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    # Update quests
    update_quest_progress(session, user_id, "CLICK", 1)
    session.close()

async def mine_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    user = get_user(session, user_id)
    inventory = get_user_inventory(session, user_id)
    
    coins, electricity, diamonds, error = calculate_mining_rewards(user, inventory, datetime.now())
    
    if error:
        await query.answer(f"❌ خطا: {error}", show_alert=True)
        session.close()
        return
    
    user.coins += coins
    user.electricity -= electricity
    user.diamonds += diamonds
    user.last_mined_at = datetime.now()
    
    session.commit()
    
    await query.answer(f"⛏ استخراج موفق!\n💰 سکه: {coins}\n🔌 برق مصرفی: {electricity}\n💎 الماس: {diamonds}", show_alert=True)
    
    # Update UI
    from utils.formatters import format_user_profile
    await query.edit_message_text(
        format_user_profile(user),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    update_quest_progress(session, user_id, "MINE", coins)
    session.close()
