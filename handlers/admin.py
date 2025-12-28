from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.models import GameItem, ItemType
from config import ADMIN_IDS

async def admin_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    # Basic implementation of adding an item via command: /additem name code type price
    try:
        args = context.args
        name = args[0]
        code = args[1]
        itype = ItemType(args[2].upper())
        price = int(args[3])
        
        session = get_session()
        item = GameItem(name=name, item_code=code, item_type=itype, price_diamonds=price)
        session.add(item)
        session.commit()
        await update.message.reply_text(f"✅ آیتم {name} با موفقیت اضافه شد!")
        session.close()
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
        
    session = get_session()
    from database.models import User
    user_count = session.query(User).count()
    await update.message.reply_text(f"📊 آمار کل بازیکنان: {user_count}")
    session.close()
