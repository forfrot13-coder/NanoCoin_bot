from telegram import Update
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user, get_all_items, get_item_by_id, add_to_inventory
from utils.keyboards import shop_keyboard, back_to_main_keyboard
from utils.formatters import format_item_details
from config import MSG_SHOP_WELCOME

async def shop_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = get_session()
    items = get_all_items(session)
    
    await query.edit_message_text(
        MSG_SHOP_WELCOME,
        reply_markup=shop_keyboard(items),
        parse_mode="Markdown"
    )
    session.close()

async def shop_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    session = get_session()
    user = get_user(session, user_id)
    item = get_item_by_id(session, item_id)
    
    if not item:
        await query.answer("آیتم یافت نشد!")
        session.close()
        return
        
    if user.diamonds < item.price_diamonds:
        await query.answer("الماس کافی ندارید! 💎", show_alert=True)
        session.close()
        return
    
    user.diamonds -= item.price_diamonds
    add_to_inventory(session, user_id, item.id)
    
    session.commit()
    await query.answer(f"✅ {item.name} با موفقیت خریداری شد!")
    
    # Refresh shop
    items = get_all_items(session)
    await query.edit_message_text(
        MSG_SHOP_WELCOME,
        reply_markup=shop_keyboard(items),
        parse_mode="Markdown"
    )
    session.close()
