import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from sqlalchemy import func, desc, and_, or_
from database.connection import get_session
from database.models import User, GameItem, Inventory, MarketListing, Achievement, UserAchievement, UserQuest, PromoCode
from database.admin_models import JoinRequirement, AdminLog, AdminSettings, BroadcastMessage, BannedUser, UserWarning
from config import ADMIN_IDS
from utils.admin_keyboards import (
    admin_main_keyboard, admin_stats_keyboard, admin_users_keyboard,
    admin_items_keyboard, admin_broadcast_keyboard, admin_join_keyboard,
    admin_settings_keyboard, admin_monitoring_keyboard, admin_logs_keyboard,
    admin_back_keyboard, admin_user_list_keyboard, admin_user_detail_keyboard,
    admin_item_list_keyboard, admin_item_detail_keyboard, admin_confirm_keyboard,
    admin_economy_keyboard, admin_join_list_keyboard, admin_join_detail_keyboard,
    admin_broadcast_confirm_keyboard, admin_help_keyboard
)
from utils.admin_helpers import (
    is_admin, is_super_admin, get_admin_level, log_admin_action,
    get_admin_setting, set_admin_setting, format_number, format_coins,
    format_diamonds, format_datetime, safe_int, safe_float, format_user_info,
    get_command_args, validate_user_id, get_user_display_name, truncate_text
)

logger = logging.getLogger(__name__)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور اصلی پنل ادمین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔️ شما دسترسی به پنل ادمین ندارید.")
        return
    
    text = """
🔐 **پنل مدیریت نانوکوین**

به پنل ادمین خوش آمدید!
لطفاً یکی از گزینه‌های زیر را انتخاب کنید:

📊 آمار و تحلیل
👥 مدیریت کاربران
🎮 مدیریت آیتم‌ها
📢 ارسال همگانی
🔗 مدیریت جوین
⚙️ تنظیمات
🔍 نظارت بر سیستم
📋 لاگ‌ها
"""
    await update.message.reply_text(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کال‌بک پنل ادمین"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("⛔️ شما دسترسی به پنل ادمین ندارید.")
        return
    
    data = query.data
    
    if data == "admin_main":
        await show_admin_main(query)
    elif data == "admin_stats":
        await show_admin_stats(query)
    elif data == "admin_users":
        await show_admin_users(query)
    elif data == "admin_items":
        await show_admin_items(query)
    elif data == "admin_broadcast":
        await show_admin_broadcast(query)
    elif data == "admin_join":
        await show_admin_join(query)
    elif data == "admin_settings":
        await show_admin_settings(query)
    elif data == "admin_monitoring":
        await show_admin_monitoring(query)
    elif data == "admin_logs":
        await show_admin_logs(query)
    elif data == "admin_economy":
        await show_admin_economy(query)
    elif data == "admin_exit":
        await query.edit_message_text("👋 پنل ادمین بسته شد.")
    elif data.startswith("admin_users_page_"):
        await show_users_page(query, int(data.split("_")[-1]))
    elif data.startswith("admin_user_view_"):
        await show_user_detail(query, int(data.split("_")[-1]))
    elif data.startswith("admin_items_page_"):
        await show_items_page(query, int(data.split("_")[-1]))
    elif data.startswith("admin_item_view_"):
        await show_item_detail(query, int(data.split("_")[-1]))
    elif data.startswith("admin_join_list"):
        await show_join_list(query)
    elif data.startswith("admin_join_view_"):
        await show_join_detail(query, int(data.split("_")[-1]))
    elif data == "admin_cancel":
        await show_admin_main(query)
    elif data == "admin_help":
        await show_admin_help(query)


async def show_admin_main(query):
    """نمایش منوی اصلی"""
    text = """
🔐 **پنل مدیریت نانوکوین**

به پنل ادمین خوش آمدید!
لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_main_keyboard(), parse_mode="Markdown")


async def show_admin_stats(query):
    """نمایش آمار و تحلیل"""
    session = get_session()
    try:
        total_users = session.query(User).count()
        active_users = session.query(User).filter(User.coins > 0).count()
        today = datetime.now().date()
        new_users = session.query(User).filter(func.date(User.created_at) == today).count()
        
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0
        total_items = session.query(GameItem).count()
        
        text = f"""
📊 **آمار و تحلیل**

👥 **کاربران:**
• کل کاربران: {format_number(total_users)}
• کاربران فعال: {format_number(active_users)}
• کاربران جدید امروز: {format_number(new_users)}

💰 **اقتصاد:**
• کل سکه در بازی: {format_coins(total_coins)}
• کل الماس در بازی: {format_diamonds(total_diamonds)}

🎮 **آیتم‌ها:**
• تعداد آیتم‌ها: {total_items}
"""
        await query.edit_message_text(text, reply_markup=admin_stats_keyboard(), parse_mode="Markdown")
    finally:
        session.close()


async def show_admin_users(query):
    """نمایش مدیریت کاربران"""
    text = """
👥 **مدیریت کاربران**

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_users_keyboard(), parse_mode="Markdown")


async def show_users_page(query, page: int = 1):
    """نمایش صفحه لیست کاربران"""
    session = get_session()
    try:
        per_page = 10
        total = session.query(User).count()
        total_pages = (total + per_page - 1) // per_page
        
        users = session.query(User).order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        if not users:
            text = "📋 هیچ کاربری یافت نشد."
            await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_users"))
            return
        
        text = f"👥 **لیست کاربران** (صفحه {page} از {total_pages})"
        await query.edit_message_text(text, reply_markup=admin_user_list_keyboard(users, page, total_pages), parse_mode="Markdown")
    finally:
        session.close()


async def show_user_detail(query, user_id: int):
    """نمایش جزئیات کاربر"""
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            await query.edit_message_text("❌ کاربر یافت نشد.", reply_markup=admin_back_keyboard("admin_users"))
            return
        
        inventory_count = session.query(Inventory).filter(Inventory.user_id == user_id).count()
        achievements_count = session.query(UserAchievement).filter(UserAchievement.user_id == user_id).count()
        quests_count = session.query(UserQuest).filter(UserQuest.user_id == user_id, UserQuest.completed == False).count()
        
        text = f"""
👤 **جزئیات کاربر**

{format_user_info(user)}

📦 موجودی: {inventory_count} آیتم
🏆 دستاوردها: {achievements_count}
🎯 ماموریت‌های فعال: {quests_count}

📅 عضویت: {format_datetime(user.created_at)}
"""
        await query.edit_message_text(text, reply_markup=admin_user_detail_keyboard(user_id), parse_mode="Markdown")
    finally:
        session.close()


async def show_admin_items(query):
    """نمایش مدیریت آیتم‌ها"""
    session = get_session()
    try:
        total_items = session.query(GameItem).count()
        text = f"""
🎮 **مدیریت آیتم‌ها**

تعداد کل آیتم‌ها: {total_items}

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
"""
        await query.edit_message_text(text, reply_markup=admin_items_keyboard(), parse_mode="Markdown")
    finally:
        session.close()


async def show_items_page(query, page: int = 1):
    """نمایش صفحه لیست آیتم‌ها"""
    session = get_session()
    try:
        per_page = 10
        total = session.query(GameItem).count()
        total_pages = (total + per_page - 1) // per_page
        
        items = session.query(GameItem).order_by(GameItem.id).offset((page - 1) * per_page).limit(per_page).all()
        
        if not items:
            text = "📋 هیچ آیتمی یافت نشد."
            await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_items"))
            return
        
        text = f"🎮 **لیست آیتم‌ها** (صفحه {page} از {total_pages})"
        await query.edit_message_text(text, reply_markup=admin_item_list_keyboard(items, page, total_pages), parse_mode="Markdown")
    finally:
        session.close()


async def show_item_detail(query, item_id: int):
    """نمایش جزئیات آیتم"""
    session = get_session()
    try:
        item = session.query(GameItem).filter(GameItem.id == item_id).first()
        if not item:
            await query.edit_message_text("❌ آیتم یافت نشد.", reply_markup=admin_back_keyboard("admin_items"))
            return
        
        text = f"""
🎮 **جزئیات آیتم**

📛 نام: {item.name}
🆔 کد: {item.item_code}
📦 نوع: {item.item_type.value}
💰 قیمت: {item.price_diamonds} 💎
💵 قیمت فروش: {item.sell_price} 💎
📊 موجودی: {'نامحدود' if item.stock == -1 else item.stock}
⛏️ قدرت ماینینگ: {item.mining_rate}
⚡ مصرف برق: {item.electricity_consumption}
"""
        await query.edit_message_text(text, reply_markup=admin_item_detail_keyboard(item_id), parse_mode="Markdown")
    finally:
        session.close()


async def show_admin_broadcast(query):
    """نمایش ارسال همگانی"""
    text = """
📢 **ارسال همگانی**

از این بخش می‌توانید پیام‌های همگانی به کاربران ارسال کنید.
لطفاً نوع ارسال را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_broadcast_keyboard(), parse_mode="Markdown")


async def show_admin_join(query):
    """نمایش مدیریت جوین"""
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        active_count = sum(1 for r in requirements if r.is_active)
        
        text = f"""
🔗 **مدیریت عضویت اجباری**

📊 وضعیت کلی:
• کل الزامات: {len(requirements)}
• فعال: {active_count}
• غیرفعال: {len(requirements) - active_count}

از این بخش می‌توانید گروه‌ها و کانال‌های الزامی را مدیریت کنید.
"""
        await query.edit_message_text(text, reply_markup=admin_join_keyboard(), parse_mode="Markdown")
    finally:
        session.close()


async def show_join_list(query):
    """نمایش لیست الزامات جوین"""
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        
        if not requirements:
            text = "📋 هیچ الزام جوینی تنظیم نشده است."
            await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_join"))
            return
        
        text = "📋 **لیست الزامات جوین**"
        await query.edit_message_text(text, reply_markup=admin_join_list_keyboard(requirements), parse_mode="Markdown")
    finally:
        session.close()


async def show_join_detail(query, req_id: int):
    """نمایش جزئیات الزام جوین"""
    session = get_session()
    try:
        req = session.query(JoinRequirement).filter(JoinRequirement.id == req_id).first()
        if not req:
            await query.edit_message_text("❌ الزام جوین یافت نشد.", reply_markup=admin_back_keyboard("admin_join_list"))
            return
        
        status = "✅ فعال" if req.is_active else "❌ غیرفعال"
        text = f"""
🔗 **جزئیات الزام جوین**

📛 نام: {req.chat_name}
🆔 آیدی: {req.chat_id}
📦 نوع: {req.chat_type}
📊 وضعیت: {status}

📝 **پیام:**
{req.message or 'پیام پیش‌فرض'}

⏰ ایجاد شده: {format_datetime(req.created_at)}
"""
        await query.edit_message_text(text, reply_markup=admin_join_detail_keyboard(req_id, req.is_active), parse_mode="Markdown")
    finally:
        session.close()


async def show_admin_settings(query):
    """نمایش تنظیمات"""
    text = """
⚙️ **تنظیمات**

لطفاً یکی از بخش‌های تنظیمات را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_settings_keyboard(), parse_mode="Markdown")


async def show_admin_monitoring(query):
    """نمایش نظارت بر سیستم"""
    text = """
🔍 **نظارت بر سیستم**

📊 آمار و وضعیت ربات:

• وضعیت: 🟢 فعال
• زمان فعالیت: 99.9%
• نسخه: 1.0.0

لطفاً یکی از گزینه‌ها را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_monitoring_keyboard(), parse_mode="Markdown")


async def show_admin_logs(query):
    """نمایش لاگ‌ها"""
    text = """
📋 **لاگ‌های مدیریت**

لطفاً نوع لاگ مورد نظر را انتخاب کنید:
"""
    await query.edit_message_text(text, reply_markup=admin_logs_keyboard(), parse_mode="Markdown")


async def show_admin_economy(query):
    """نمایش مدیریت اقتصاد"""
    text = """
💎 **مدیریت اقتصاد**

از این بخش می‌توانید سکه و الماس کل بازی را مدیریت کنید.

⚠️ توجه: این عملیات روی تمام کاربران تاثیر می‌گذارد.
"""
    await query.edit_message_text(text, reply_markup=admin_economy_keyboard(), parse_mode="Markdown")


async def show_admin_help(query):
    """نمایش راهنما"""
    text = """
📚 **راهنمای پنل ادمین**

**دستورات اصلی:**
/admin - باز کردن پنل ادمین
/admin_users - مدیریت کاربران
/admin_items - مدیریت آیتم‌ها
/admin_stats - مشاهده آمار
/admin_broadcast - ارسال همگانی
/admin_join - مدیریت جوین

**نکات مهم:**
• تمام عملیات در لاگ ثبت می‌شود
• قبل از حذف کاربر، اطمینان حاصل کنید
• برای ارسال همگانی، پیام را دوباره بررسی کنید
"""
    await query.edit_message_text(text, reply_markup=admin_help_keyboard(), parse_mode="Markdown")


# ========== ADMIN COMMANDS ==========

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور مدیریت کاربران"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    text = """
👥 **مدیریت کاربران**

دستورات:
• /admin_search_user [یوزرنیم/آیدی] - جستجوی کاربر
• /admin_view_user [آیدی] - مشاهده کاربر
• /admin_ban_user [آیدی] - مسدود کردن
• /admin_unban_user [آیدی] - رفع مسدودی
• /admin_give_coins [آیدی] [مقدار] - دادن سکه
• /admin_give_diamonds [آیدی] [مقدار] - دادن الماس
• /admin_reset_user [آیدی] - ریست کاربر
• /admin_delete_user [آیدی] - حذف کاربر
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_items_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور مدیریت آیتم‌ها"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    text = """
🎮 **مدیریت آیتم‌ها**

دستورات:
• /admin_add_item [نام] [کد] [نوع] [قیمت] - اضافه کردن
• /admin_edit_item [آیدی] - ویرایش
• /admin_delete_item [آیدی] - حذف
• /admin_set_price [آیدی] [قیمت] - تنظیم قیمت
• /admin_set_stock [آیدی] [تعداد] - تنظیم موجودی
• /admin_toggle_item [آیدی] - فعال/غیرفعال
• /admin_item_stats - آمار آیتم‌ها

انواع آیتم: MINER, BUFF, SKIN, AVATAR, ENERGY
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور مشاهده آمار"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        total_users = session.query(User).count()
        active_users = session.query(User).filter(User.coins > 0).count()
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0
        total_items = session.query(GameItem).count()
        total_listings = session.query(MarketListing).count()
        
        text = f"""
📊 **آمار کامل بازی**

👥 **کاربران:**
• کل: {format_number(total_users)}
• فعال: {format_number(active_users)}
• نرخ فعالیت: {(active_users/total_users*100) if total_users > 0 else 0:.1f}%

💰 **اقتصاد:**
• کل سکه: {format_coins(total_coins)}
• کل الماس: {format_diamonds(total_diamonds)}
• میانگین سکه: {format_coins(total_coins//total_users) if total_users > 0 else 0}

🎮 **آیتم‌ها:**
• تعداد آیتم‌ها: {total_items}
• آگهی‌های بازار: {total_listings}
"""
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def admin_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور جدول برترین‌ها"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        top_users = session.query(User).order_by(User.coins.desc()).limit(10).all()
        
        text = "🏆 **جدول برترین‌ها**\n\n"
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {user.first_name[:15]}: {format_coins(user.coins)}\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def admin_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجوی کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ لطفاً یوزرنیم یا آیدی کاربر را وارد کنید.\nمثال: /admin_search_user 123456")
        return
    
    query_str = args[0]
    session = get_session()
    try:
        user = None
        if query_str.isdigit():
            user = session.query(User).filter(User.user_id == int(query_str)).first()
        else:
            if query_str.startswith('@'):
                query_str = query_str[1:]
            user = session.query(User).filter(User.username == query_str).first()
        
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        text = f"""
👤 **کاربر یافت شد:**

{format_user_info(user)}

📅 عضویت: {format_datetime(user.created_at)}
"""
        await update.message.reply_text(text, parse_mode="Markdown")
        await log_admin_action(update, "search_user", "user", str(user.user_id), f"Searched for {query_str}")
    finally:
        session.close()


async def admin_give_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دادن سکه به کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_give_coins [آیدی] [مقدار]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    amount = safe_int(args[1], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return
    
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        user.coins += amount
        session.commit()
        
        await update.message.reply_text(f"✅ {format_coins(amount)} به {user.first_name} داده شد.")
        await log_admin_action(update, "give_coins", "user", str(target_id), f"Gave {format_coins(amount)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_give_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دادن الماس به کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_give_diamonds [آیدی] [مقدار]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    amount = safe_int(args[1], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return
    
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        user.diamonds += amount
        session.commit()
        
        await update.message.reply_text(f"✅ {format_diamonds(amount)} به {user.first_name} داده شد.")
        await log_admin_action(update, "give_diamonds", "user", str(target_id), f"Gave {format_diamonds(amount)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مسدود کردن کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_ban_user [آیدی] [دلیل]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    reason = " ".join(args[1:]) if len(args) > 1 else "بدون دلیل"
    
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        # اضافه کردن به لیست مسدود
        banned = BannedUser(
            user_id=target_id,
            username=user.username,
            first_name=user.first_name,
            reason=reason,
            banned_by=user_id,
            is_permanent=True
        )
        session.add(banned)
        
        # ریست کردن دارایی کاربر
        user.coins = 0
        user.diamonds = 0
        
        session.commit()
        
        await update.message.reply_text(f"✅ کاربر {user.first_name} مسدود شد.\n📝 دلیل: {reason}")
        await log_admin_action(update, "ban_user", "user", str(target_id), f"Banned. Reason: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفع مسدودی کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_unban_user [آیدی]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    session = get_session()
    try:
        banned = session.query(BannedUser).filter(BannedUser.user_id == target_id).first()
        if not banned:
            await update.message.reply_text("❌ این کاربر مسدود نیست.")
            return
        
        session.delete(banned)
        session.commit()
        
        await update.message.reply_text(f"✅ مسدودی کاربر برطرف شد.")
        await log_admin_action(update, "unban_user", "user", str(target_id), "Unbanned user")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست کردن کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_reset_user [آیدی]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        # ریست کردن دارایی‌ها
        user.coins = 0
        user.diamonds = 0
        user.energy = 1000
        user.max_energy = 1000
        user.electricity = 5000
        user.max_electricity = 5000
        user.click_level = 1
        user.click_xp = 0
        user.active_boost_until = None
        user.boost_multiplier = 1.0
        user.slot_1_id = None
        user.slot_2_id = None
        user.slot_3_id = None
        user.daily_streak = 0
        
        # حذف آیتم‌های انventory
        session.query(Inventory).filter(Inventory.user_id == target_id).delete()
        
        session.commit()
        
        await update.message.reply_text(f"✅ کاربر {user.first_name} ریست شد.")
        await log_admin_action(update, "reset_user", "user", str(target_id), "Reset user data")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کاربر"""
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند کاربر را حذف کند.")
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_delete_user [آیدی]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return
        
        username = user.first_name
        
        # حذف تمام داده‌های مرتبط
        session.query(Inventory).filter(Inventory.user_id == target_id).delete()
        session.query(UserAchievement).filter(UserAchievement.user_id == target_id).delete()
        session.query(UserQuest).filter(UserQuest.user_id == target_id).delete()
        session.query(MarketListing).filter(MarketListing.seller_id == target_id).delete()
        session.query(User).filter(User.user_id == target_id).delete()
        
        session.commit()
        
        await update.message.reply_text(f"✅ کاربر {username} و تمام داده‌های آن حذف شد.")
        await log_admin_action(update, "delete_user", "user", str(target_id), "Deleted user and all data")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


# ========== JOIN MANAGEMENT COMMANDS ==========

async def admin_join_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن گروه/کانال به الزامات جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 1:
        await update.message.reply_text("""
❌ فرمت صحیح: /admin_join_add [چت آیدی] [نام]

مثال:
/admin_join_add -1001234567890 "گروه بازیکنان"
/admin_join_add -1001234567890
""")
        return
    
    chat_id = args[0]
    chat_name = " ".join(args[1:]) if len(args) > 1 else "گروه/کانال"
    
    session = get_session()
    try:
        # بررسی وجود قبلی
        existing = session.query(JoinRequirement).filter(JoinRequirement.chat_id == chat_id).first()
        if existing:
            await update.message.reply_text("❌ این گروه/کانال قبلاً اضافه شده است.")
            return
        
        req = JoinRequirement(
            chat_id=chat_id,
            chat_name=chat_name,
            chat_type="SUPERGROUP",
            message=f"لطفاً در {chat_name} عضو شوید تا بتوانید بازی کنید.",
            is_active=True,
            created_by=user_id
        )
        session.add(req)
        session.commit()
        
        await update.message.reply_text(f"""
✅ **گروه/کانال اضافه شد!**

📛 نام: {chat_name}
🆔 آیدی: {chat_id}
📊 وضعیت: فعال
""", parse_mode="Markdown")
        await log_admin_action(update, "join_add", "group", chat_id, f"Added group {chat_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_join_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف گروه/کانال از الزامات جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_remove [چت آیدی]")
        return
    
    chat_id = args[0]
    
    session = get_session()
    try:
        req = session.query(JoinRequirement).filter(JoinRequirement.chat_id == chat_id).first()
        if not req:
            await update.message.reply_text("❌ این گروه/کانال یافت نشد.")
            return
        
        chat_name = req.chat_name
        session.delete(req)
        session.commit()
        
        await update.message.reply_text(f"✅ {chat_name} از لیست الزامات حذف شد.")
        await log_admin_action(update, "join_remove", "group", chat_id, f"Removed group {chat_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_join_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست گروه‌ها/کانال‌های الزامی"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        
        if not requirements:
            await update.message.reply_text("📋 هیچ الزام جوینی تنظیم نشده است.")
            return
        
        text = "📋 **لیست الزامات جوین:**\n\n"
        for req in requirements:
            status = "✅" if req.is_active else "❌"
            text += f"{status} {req.chat_name} ({req.chat_id})\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def admin_join_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم پیام جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_message [چت آیدی] [پیام]")
        return
    
    chat_id = args[0]
    message = " ".join(args[1:])
    
    session = get_session()
    try:
        req = session.query(JoinRequirement).filter(JoinRequirement.chat_id == chat_id).first()
        if not req:
            await update.message.reply_text("❌ این گروه/کانال یافت نشد.")
            return
        
        req.message = message
        session.commit()
        
        await update.message.reply_text(f"✅ پیام به‌روزرسانی شد.\n\n📝 پیام جدید:\n{message}")
        await log_admin_action(update, "join_message", "group", chat_id, "Updated join message")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_join_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیمات جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    text = """
⚙️ **تنظیمات عضویت اجباری**

دستورات:
• /admin_join_add [آیدی] [نام] - اضافه کردن
• /admin_join_remove [آیدی] - حذف کردن
• /admin_join_list - لیست
• /admin_join_message [آیدی] [پیام] - تنظیم پیام
• /admin_join_toggle [آیدی] - فعال/غیرفعال
• /admin_join_test [آیدی کاربر] - تست بررسی

📝 وقتی کاربر /start می‌زند، بررسی می‌شود که آیا در گروه‌های مشخص شده عضو است یا خیر.
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_join_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال/غیرفعال کردن الزام جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_toggle [چت آیدی]")
        return
    
    chat_id = args[0]
    
    session = get_session()
    try:
        req = session.query(JoinRequirement).filter(JoinRequirement.chat_id == chat_id).first()
        if not req:
            await update.message.reply_text("❌ این گروه/کانال یافت نشد.")
            return
        
        req.is_active = not req.is_active
        status = "فعال" if req.is_active else "غیرفعال"
        session.commit()
        
        await update.message.reply_text(f"✅ وضعیت به {status} تغییر کرد.")
        await log_admin_action(update, "join_toggle", "group", chat_id, f"Toggled to {status}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


# ========== BROADCAST COMMANDS ==========

async def admin_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام همگانی"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if not args:
        await update.message.reply_text("""
📢 **ارسال همگانی**

دستورات:
• /admin_broadcast [پیام] - ارسال پیام متنی
• /admin_dm [آیدی] [پیام] - ارسال پیام خصوصی
• /admin_announce [عنوان] [پیام] - ارسال اعلامیه
• /admin_scheduled [زمان] [پیام] - ارسال زمان‌بندی شده

مثال:
/admin_broadcast سلام به همه بازیکنان!
""")
        return
    
    message = " ".join(args)
    
    session = get_session()
    try:
        users = session.query(User).all()
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(chat_id=user.user_id, text=message)
                success += 1
            except Exception:
                failed += 1
        
        await update.message.reply_text(f"""
📢 **ارسال همگانی انجام شد**

✅ موفق: {success}
❌ ناموفق: {failed}
""", parse_mode="Markdown")
        await log_admin_action(update, "broadcast", "users", str(success), f"Sent broadcast to {success} users")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خصوصی به کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_dm [آیدی] [پیام]")
        return
    
    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    message = " ".join(args[1:])
    
    try:
        await context.bot.send_message(chat_id=target_id, text=message)
        await update.message.reply_text(f"✅ پیام به کاربر {target_id} ارسال شد.")
        await log_admin_action(update, "dm", "user", str(target_id), "Sent direct message")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال اعلامیه"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_announce [عنوان] [پیام]")
        return
    
    title = args[0]
    message = " ".join(args[1:])
    
    full_message = f"""
📢 **اعلامیه**

🏷️ {title}

{message}
"""
    
    session = get_session()
    try:
        users = session.query(User).all()
        success = 0
        
        for user in users:
            try:
                await context.bot.send_message(chat_id=user.user_id, text=full_message, parse_mode="Markdown")
                success += 1
            except Exception:
                pass
        
        await update.message.reply_text(f"✅ اعلامیه به {success} کاربر ارسال شد.")
        await log_admin_action(update, "announce", "users", str(success), f"Announcement: {title}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


# ========== ITEM MANAGEMENT COMMANDS ==========

async def admin_add_item_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن آیتم"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 4:
        await update.message.reply_text("""
❌ فرمت صحیح: /admin_add_item [نام] [کد] [نوع] [قیمت]

مثال:
/admin_add_item ماینر طلایی gold_miner MINER 100

انواع: MINER, BUFF, SKIN, AVATAR, ENERGY
""")
        return
    
    name = args[0]
    code = args[1]
    item_type = args[2].upper()
    price = safe_int(args[3], 0)
    
    try:
        from database.models import ItemType
        itype = ItemType(item_type)
    except ValueError:
        await update.message.reply_text("❌ نوع آیتم نامعتبر است.")
        return
    
    session = get_session()
    try:
        item = GameItem(name=name, item_code=code, item_type=itype, price_diamonds=price)
        session.add(item)
        session.commit()
        
        await update.message.reply_text(f"✅ آیتم {name} با موفقیت اضافه شد!")
        await log_admin_action(update, "add_item", "item", str(item.id), f"Added item {name}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم قیمت آیتم"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_set_price [آیدی] [قیمت]")
        return
    
    item_id = safe_int(args[0], 0)
    price = safe_int(args[1], 0)
    
    session = get_session()
    try:
        item = session.query(GameItem).filter(GameItem.id == item_id).first()
        if not item:
            await update.message.reply_text("❌ آیتم یافت نشد.")
            return
        
        old_price = item.price_diamonds
        item.price_diamonds = price
        session.commit()
        
        await update.message.reply_text(f"✅ قیمت {item.name} از {old_price} به {price} تغییر کرد.")
        await log_admin_action(update, "set_price", "item", str(item_id), f"Changed price from {old_price} to {price}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


# ========== ADDITIONAL ADMIN FUNCTIONS ==========

async def admin_item_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار آیتم‌ها"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        from database.models import ItemType
        
        miners = session.query(GameItem).filter(GameItem.item_type == ItemType.MINER).count()
        buffs = session.query(GameItem).filter(GameItem.item_type == ItemType.BUFF).count()
        skins = session.query(GameItem).filter(GameItem.item_type == ItemType.SKIN).count()
        
        total_stock = session.query(func.sum(GameItem.stock)).filter(GameItem.stock > 0).scalar() or 0
        
        text = f"""
📊 **آمار آیتم‌ها**

🎮 انواع آیتم:
• ماینر: {miners}
• باف: {buffs}
• اسکین: {skins}

📦 موجودی کل: {total_stock if total_stock > 0 else 'نامحدود'}
"""
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def admin_active_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست کاربران فعال"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        # کاربران فعال در 24 ساعت اخیر
        yesterday = datetime.now() - timedelta(days=1)
        active_users = session.query(User).filter(User.updated_at >= yesterday).count()
        
        # کاربران با بیش از 10000 سکه
        rich_users = session.query(User).filter(User.coins > 10000).count()
        
        text = f"""
📈 **آمار کاربران فعال**

⏰ **24 ساعت اخیر:**
• کاربران فعال: {active_users}

💰 **ثروتمندان:**
• کاربران با بیش از 10K سکه: {rich_users}

🏆 **کاربران برتر:**
"""
        
        top_users = session.query(User).order_by(User.coins.desc()).limit(5).all()
        for i, user in enumerate(top_users, 1):
            text += f"{i}. {user.first_name}: {format_coins(user.coins)}\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


# ========== CALLBACK QUERY HANDLERS ==========

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت تمام کال‌بک‌های ادمین"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("⛔️ شما ادمین نیستید!")
        return
    
    data = query.data
    
    # مدیریت کاربر
    if data.startswith("admin_user_"):
        await handle_user_callback(query, data)
    # مدیریت آیتم
    elif data.startswith("admin_item_"):
        await handle_item_callback(query, data)
    # مدیریت جوین
    elif data.startswith("admin_join_"):
        await handle_join_callback(query, data)
    # مدیریت برگشت
    elif data.startswith("admin_"):
        await admin_panel_callback(update, context)


async def handle_user_callback(query, data):
    """مدیریت کال‌بک‌های کاربر"""
    parts = data.split("_")
    action = parts[2] if len(parts) > 2 else ""
    
    if len(parts) < 4:
        return
    
    user_id = int(parts[3])
    
    if action == "view":
        await show_user_detail(query, user_id)
    elif action in ["give", "ban", "unban", "reset", "delete"]:
        await query.edit_message_text(f"⚠️ برای {action} کاربر، لطفاً از دستور استفاده کنید:\n/admin_{action}_user {user_id}")


async def handle_item_callback(query, data):
    """مدیریت کال‌بک‌های آیتم"""
    parts = data.split("_")
    action = parts[2] if len(parts) > 2 else ""
    
    if len(parts) < 4:
        return
    
    item_id = int(parts[3])
    
    if action == "view":
        await show_item_detail(query, item_id)
    elif action in ["edit", "price", "stock", "toggle", "delete"]:
        await query.edit_message_text(f"⚠️ برای {action} آیتم، لطفاً از دستور استفاده کنید.")


async def handle_join_callback(query, data):
    """مدیریت کال‌بک‌های جوین"""
    parts = data.split("_")
    action = parts[2] if len(parts) > 2 else ""
    
    if action == "list":
        await show_join_list(query)
    elif len(parts) >= 4:
        req_id = int(parts[3])
        if action == "view":
            await show_join_detail(query, req_id)


# ========== REGISTER ADMIN HANDLERS ==========

def register_admin_handlers(application):
    """ثبت تمام هندلرهای ادمین"""
    
    # دستورات
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_items", admin_items_cmd))
    application.add_handler(CommandHandler("admin_stats", admin_stats_cmd))
    application.add_handler(CommandHandler("admin_leaderboard", admin_leaderboard))
    application.add_handler(CommandHandler("admin_search_user", admin_search_user))
    application.add_handler(CommandHandler("admin_give_coins", admin_give_coins))
    application.add_handler(CommandHandler("admin_give_diamonds", admin_give_diamonds))
    application.add_handler(CommandHandler("admin_ban_user", admin_ban_user))
    application.add_handler(CommandHandler("admin_unban_user", admin_unban_user))
    application.add_handler(CommandHandler("admin_reset_user", admin_reset_user))
    application.add_handler(CommandHandler("admin_delete_user", admin_delete_user))
    
    # آیتم‌ها
    application.add_handler(CommandHandler("admin_add_item", admin_add_item_cmd))
    application.add_handler(CommandHandler("admin_set_price", admin_set_price))
    application.add_handler(CommandHandler("admin_item_stats", admin_item_stats))
    
    # جوین
    application.add_handler(CommandHandler("admin_join", admin_join_settings))
    application.add_handler(CommandHandler("admin_join_add", admin_join_add))
    application.add_handler(CommandHandler("admin_join_remove", admin_join_remove))
    application.add_handler(CommandHandler("admin_join_list", admin_join_list))
    application.add_handler(CommandHandler("admin_join_message", admin_join_message))
    application.add_handler(CommandHandler("admin_join_toggle", admin_join_toggle))
    
    # ارسال همگانی
    application.add_handler(CommandHandler("admin_broadcast", admin_broadcast_cmd))
    application.add_handler(CommandHandler("admin_dm", admin_dm))
    application.add_handler(CommandHandler("admin_announce", admin_announce))
    
    # آمار
    application.add_handler(CommandHandler("admin_active_users", admin_active_users))
    
    # کال‌بک‌ها
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
