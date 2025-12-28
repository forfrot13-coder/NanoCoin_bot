from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_achievements, get_user_achievements
from utils.keyboards import back_to_main_keyboard

async def achievements_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    all_achievements = get_achievements(session)
    user_achievements = {ua.achievement_id for ua in get_user_achievements(session, user_id)}
    
    text = "🏆 *دستاوردها:*\n\n"
    for ach in all_achievements:
        status = "✅" if ach.id in user_achievements else "🔒"
        text += f"{status} *{ach.title}* ({ach.emoji})\n"
        text += f"📝 {ach.description}\n\n"
        
    await query.edit_message_text(text, reply_markup=back_to_main_keyboard(), parse_mode="Markdown")
    session.close()
