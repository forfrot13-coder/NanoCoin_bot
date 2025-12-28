from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user, create_user
from utils.keyboards import main_menu_keyboard
from config import MSG_START, MSG_REGISTERED

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    session = get_session()
    user = get_user(session, user_id)
    
    if not user:
        create_user(session, user_id, username, first_name)
        await update.message.reply_text(MSG_REGISTERED)
    
    await update.message.reply_text(MSG_START, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    session.close()

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(MSG_START, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
