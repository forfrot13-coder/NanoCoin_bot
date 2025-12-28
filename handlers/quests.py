from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user_quests
from utils.keyboards import back_to_main_keyboard

async def quests_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    quests = get_user_quests(session, user_id)
    
    if not quests:
        text = "🎯 فعلاً ماموریت فعالی ندارید!"
    else:
        text = "🎯 *ماموریت‌های امروز:*\n\n"
        for q in quests:
            status = "✅" if q.completed else "⏳"
            text += f"{status} *{q.title}*\n"
            text += f"📊 پیشرفت: `{q.progress}/{q.goal}`\n"
            text += f"💰 پاداش: `{q.reward_coins} سکه` | `{q.reward_diamonds} الماس`\n\n"
            
    await query.edit_message_text(text, reply_markup=back_to_main_keyboard(), parse_mode="Markdown")
    session.close()
