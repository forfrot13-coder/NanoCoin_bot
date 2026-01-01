import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from backend.config import BOT_TOKEN, WEBAPP_URL
from database.connection import init_db
from database.models import User
from database.connection import get_session

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    Only purpose: Open the Web App game.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Ensure user exists in database
    session = get_session()
    try:
        db_user = session.query(User).filter(User.user_id == user_id).first()
        
        if not db_user:
            db_user = User(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            session.add(db_user)
            session.commit()
            logger.info(f"New user registered: {user_id} (@{username})")
    finally:
        session.close()
    
    # Create Web App button
    keyboard = [
        [InlineKeyboardButton(
            text="🎮 بازی کن!",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        f"🚀 به نانوکوین خوش آمدید، {first_name}!\n\n"
        "💰 یک بازی مهیج برای استخراج و جمع‌آوری سکه و الماس\n"
        "⚡️ کلیک کنید، استخراج کنید و به صدر جدول راه یابید!\n\n"
        "👇 برای شروع بازی روی دکمه زیر کلیک کنید:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    """Start the bot."""
    # Initialize Database
    init_db()
    logger.info("Database initialized")
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)
    
    # Run bot
    logger.info("Bot started - Telegram Web App launcher mode")
    application.run_polling()


if __name__ == '__main__':
    main()
