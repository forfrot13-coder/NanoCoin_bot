from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user, get_top_players, get_user_inventory
from utils.formatters import format_user_profile, format_inventory, format_leaderboard
from utils.keyboards import profile_keyboard, back_to_main_keyboard

async def profile_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    user = get_user(session, user_id)
    
    await query.edit_message_text(
        format_user_profile(user),
        reply_markup=profile_keyboard(),
        parse_mode="Markdown"
    )
    session.close()

async def inventory_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    session = get_session()
    inventory = get_user_inventory(session, user_id)
    
    keyboard = []
    for inv in inventory:
        status = "✅" if inv.is_active else "❌"
        btn_text = f"{inv.item.emoji} {inv.item.name} {status}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"inv_toggle_{inv.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="profile_main")])
    
    await query.edit_message_text(
        format_inventory(inventory),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    session.close()

async def inventory_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    inv_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    session = get_session()
    inv_item = session.query(Inventory).filter(Inventory.id == inv_id, Inventory.user_id == user_id).first()
    
    if not inv_item:
        await query.answer("آیتم یافت نشد!")
        session.close()
        return
        
    # Simple toggle logic
    inv_item.is_active = not inv_item.is_active
    
    # If it's an artifact, update user slots (simplified: just put it in the first empty slot)
    user = get_user(session, user_id)
    if inv_item.item.item_type.value == "BUFF":
        if inv_item.is_active:
            if not user.slot_1_id: user.slot_1_id = inv_item.item_id
            elif not user.slot_2_id: user.slot_2_id = inv_item.item_id
            elif not user.slot_3_id: user.slot_3_id = inv_item.item_id
            else:
                inv_item.is_active = False
                await query.answer("اسلات‌های شما پر است!", show_alert=True)
        else:
            if user.slot_1_id == inv_item.item_id: user.slot_1_id = None
            elif user.slot_2_id == inv_item.item_id: user.slot_2_id = None
            elif user.slot_3_id == inv_item.item_id: user.slot_3_id = None

    session.commit()
    await query.answer("وضعیت تغییر کرد!")
    await inventory_main(update, context)
    session.close()

async def leaderboard_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = get_session()
    top_players = get_top_players(session)
    
    await query.edit_message_text(
        format_leaderboard(top_players),
        reply_markup=back_to_main_keyboard(),
        parse_mode="Markdown"
    )
    session.close()
