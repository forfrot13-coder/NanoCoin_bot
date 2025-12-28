from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.connection import get_session
from database.queries import get_user, get_market_listings, get_listing_by_id, delete_listing, add_to_inventory
from config import MSG_MARKET_WELCOME, MARKET_TAX_PERCENT

async def market_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = get_session()
    listings = get_market_listings(session)
    
    keyboard = []
    for listing in listings:
        keyboard.append([InlineKeyboardButton(
            f"{listing.item.emoji} {listing.item.name} - {listing.price_diamonds}💎", 
            callback_data=f"market_buy_{listing.id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    
    await query.edit_message_text(
        MSG_MARKET_WELCOME,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    session.close()

async def market_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    listing_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    session = get_session()
    user = get_user(session, user_id)
    listing = get_listing_by_id(session, listing_id)
    
    if not listing:
        await query.answer("این پیشنهاد دیگر موجود نیست!")
        session.close()
        return
        
    if user.user_id == listing.seller_id:
        await query.answer("شما نمی‌توانید از خودتان خرید کنید!")
        session.close()
        return
        
    if user.diamonds < listing.price_diamonds:
        await query.answer("الماس کافی ندارید! 💎", show_alert=True)
        session.close()
        return
    
    seller = get_user(session, listing.seller_id)
    
    # Process transaction
    user.diamonds -= listing.price_diamonds
    tax = int(listing.price_diamonds * (MARKET_TAX_PERCENT / 100))
    seller.diamonds += (listing.price_diamonds - tax)
    
    add_to_inventory(session, user_id, listing.item_id, listing.quantity)
    delete_listing(session, listing.id)
    
    session.commit()
    await query.answer(f"✅ خرید موفقیت‌آمیز بود!")
    
    # Refresh market
    await market_main(update, context)
    session.close()
