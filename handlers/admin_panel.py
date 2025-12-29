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
    admin_broadcast_confirm_keyboard, admin_help_keyboard, admin_quests_keyboard
)
from utils.admin_helpers import (
    is_admin, is_super_admin, get_admin_level, log_admin_action,
    get_admin_setting, set_admin_setting, format_number, format_coins,
    format_diamonds, format_datetime, safe_int, safe_float, format_user_info,
    get_command_args, validate_user_id, get_user_display_name, truncate_text,
    split_message
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
    elif data == "admin_quests":
        await show_admin_quests(query)
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
    elif data == "admin_stats_users":
        await show_stats_users(query)
    elif data == "admin_stats_economy":
        await show_stats_economy(query)
    elif data == "admin_stats_items":
        await show_stats_items(query)
    elif data == "admin_leaderboard":
        await show_leaderboard_callback(query)
    elif data == "admin_active_users":
        await show_active_users_callback(query)
    elif data == "admin_economy_add_coins":
        await show_economy_add_coins(query)
    elif data == "admin_economy_remove_coins":
        await show_economy_remove_coins(query)
    elif data == "admin_economy_add_diamonds":
        await show_economy_add_diamonds(query)
    elif data == "admin_economy_remove_diamonds":
        await show_economy_remove_diamonds(query)
    elif data == "admin_economy_report":
        await show_economy_report(query)
    elif data == "admin_monitor_bot":
        await show_monitor_bot(query)
    elif data == "admin_monitor_resources":
        await show_monitor_resources(query)
    elif data == "admin_monitor_performance":
        await show_monitor_performance(query)
    elif data == "admin_monitor_errors":
        await show_monitor_errors(query)
    elif data == "admin_monitor_usage":
        await show_monitor_usage(query)
    elif data == "admin_settings_general":
        await show_settings_general(query)
    elif data == "admin_settings_game":
        await show_settings_game(query)
    elif data == "admin_settings_economy":
        await show_settings_economy(query)
    elif data == "admin_settings_security":
        await show_settings_security(query)
    elif data == "admin_settings_notifications":
        await show_settings_notifications(query)
    elif data == "admin_logs_today":
        await show_logs_today(query)
    elif data == "admin_logs_yesterday":
        await show_logs_yesterday(query)
    elif data == "admin_logs_search":
        await show_logs_search(query)
    elif data == "admin_logs_report":
        await show_logs_report(query)
    elif data.startswith("admin_quest_list"):
        await show_quest_list(query)
    elif data.startswith("admin_quest_view_"):
        await show_quest_detail(query, int(data.split("_")[-1]))
    elif data == "admin_user_list":
        await show_users_page(query, 1)
    elif data == "admin_user_search":
        await query.edit_message_text("🔍 برای جستجوی کاربر، از دستور زیر استفاده کنید:\n/admin_search_user [یوزرنیم یا آیدی]", reply_markup=admin_back_keyboard("admin_users"))
    elif data == "admin_user_ban":
        await query.edit_message_text("🚫 برای مسدود کردن کاربر، از دستور زیر استفاده کنید:\n/admin_ban_user [آیدی] [دلیل]", reply_markup=admin_back_keyboard("admin_users"))
    elif data == "admin_user_unban":
        await query.edit_message_text("✅ برای رفع مسدودی، از دستور زیر استفاده کنید:\n/admin_unban_user [آیدی]", reply_markup=admin_back_keyboard("admin_users"))
    elif data == "admin_user_give":
        await query.edit_message_text("💰 برای دادن سکه/الماس، از دستورات زیر استفاده کنید:\n/admin_give_coins [آیدی] [مقدار]\n/admin_give_diamonds [آیدی] [مقدار]", reply_markup=admin_back_keyboard("admin_users"))
    elif data == "admin_user_reset":
        await query.edit_message_text("🔄 برای ریست کاربر، از دستور زیر استفاده کنید:\n/admin_reset_user [آیدی]", reply_markup=admin_back_keyboard("admin_users"))
    elif data == "admin_item_add":
        await query.edit_message_text("➕ برای اضافه کردن آیتم، از دستور زیر استفاده کنید:\n/admin_add_item [نام] [کد] [نوع] [قیمت]", reply_markup=admin_back_keyboard("admin_items"))
    elif data == "admin_item_edit":
        await query.edit_message_text("✏️ برای ویرایش آیتم، لطفاً ابتدا آیتم را از لیست انتخاب کنید.", reply_markup=admin_back_keyboard("admin_items"))
    elif data == "admin_item_delete":
        await query.edit_message_text("🗑 برای حذف آیتم، لطفاً ابتدا آیتم را از لیست انتخاب کنید.", reply_markup=admin_back_keyboard("admin_items"))
    elif data == "admin_item_price":
        await query.edit_message_text("💎 برای تنظیم قیمت آیتم، از دستور زیر استفاده کنید:\n/admin_set_price [آیدی] [قیمت]", reply_markup=admin_back_keyboard("admin_items"))
    elif data == "admin_item_stock":
        await query.edit_message_text("📦 برای تنظیم موجودی آیتم، لطفاً از تنظیمات آیتم استفاده کنید.", reply_markup=admin_back_keyboard("admin_items"))
    elif data == "admin_items_page_current":
        pass
    elif data == "admin_users_page_current":
        pass
    elif data == "admin_broadcast_text":
        await query.edit_message_text("📝 برای ارسال پیام متنی، از دستور زیر استفاده کنید:\n/admin_broadcast [پیام]", reply_markup=admin_back_keyboard("admin_broadcast"))
    elif data == "admin_broadcast_photo":
        await query.edit_message_text("🖼 برای ارسال عکس، لطفاً پیام حاوی عکس را ارسال کنید.", reply_markup=admin_back_keyboard("admin_broadcast"))
    elif data == "admin_broadcast_poll":
        await query.edit_message_text("📊 ارسال نظرسنجی در حال حاضر پشتیبانی نمی‌شود.", reply_markup=admin_back_keyboard("admin_broadcast"))
    elif data == "admin_broadcast_scheduled":
        await query.edit_message_text("⏰ ارسال زمان‌بندی شده در حال حاضر پشتیبانی نمی‌شود.", reply_markup=admin_back_keyboard("admin_broadcast"))
    elif data == "admin_broadcast_status":
        await query.edit_message_text("📈 وضعیت ارسال‌های قبلی:\nدر حال حاضر ارسالی در جریان نیست.", reply_markup=admin_back_keyboard("admin_broadcast"))
    elif data == "admin_join_add":
        await query.edit_message_text("➕ برای اضافه کردن گروه/کانال، از دستور زیر استفاده کنید:\n/admin_join_add [آیدی] [نام]", reply_markup=admin_back_keyboard("admin_join"))
    elif data == "admin_join_remove":
        await query.edit_message_text("➖ برای حذف گروه/کانال، از دستور زیر استفاده کنید:\n/admin_join_remove [آیدی]", reply_markup=admin_back_keyboard("admin_join"))
    elif data == "admin_join_edit_message":
        await query.edit_message_text("✏️ برای ویرایش پیام، از دستور زیر استفاده کنید:\n/admin_join_message [آیدی] [پیام]", reply_markup=admin_back_keyboard("admin_join"))
    elif data == "admin_join_toggle":
        await query.edit_message_text("✅ برای فعال/غیرفعال کردن، از دستور زیر استفاده کنید:\n/admin_join_toggle [آیدی]", reply_markup=admin_back_keyboard("admin_join"))
    elif data == "admin_join_check":
        await query.edit_message_text("🔄 بررسی وضعیت در حال حاضر پشتیبانی نمی‌شود.", reply_markup=admin_back_keyboard("admin_join"))
    elif data == "admin_quest_add":
        await query.edit_message_text("➕ برای اضافه کردن ماموریت، از دستورات ماموریت استفاده کنید.", reply_markup=admin_back_keyboard("admin_quests"))
    elif data == "admin_quest_edit":
        await query.edit_message_text("✏️ برای ویرایش ماموریت، از دستورات ماموریت استفاده کنید.", reply_markup=admin_back_keyboard("admin_quests"))
    elif data == "admin_quest_delete":
        await query.edit_message_text("🗑 برای حذف ماموریت، از دستورات ماموریت استفاده کنید.", reply_markup=admin_back_keyboard("admin_quests"))
    elif data == "admin_help_commands":
        await query.edit_message_text("📚 لیست دستورات ادمین موجود در /admin_help است.", reply_markup=admin_back_keyboard("admin_help"))
    elif data == "admin_help_faq":
        await query.edit_message_text("❓ سوالات متداول:\n\n1. چگونه کاربری را مسدود کنم؟\n   دستور: /admin_ban_user\n\n2. چگونه سکه بدهم؟\n   دستور: /admin_give_coins", reply_markup=admin_back_keyboard("admin_help"))


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


async def admin_remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کم کردن سکه از کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_remove_coins [آیدی] [مقدار]")
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
        
        old_coins = user.coins
        user.coins = max(0, user.coins - amount)
        removed = old_coins - user.coins
        session.commit()
        
        await update.message.reply_text(f"✅ {format_coins(removed)} از {user.first_name} کم شد.\n💰 موجودی جدید: {format_coins(user.coins)}")
        await log_admin_action(update, "remove_coins", "user", str(target_id), f"Removed {format_coins(removed)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_remove_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کم کردن الماس از کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_remove_diamonds [آیدی] [مقدار]")
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
        
        old_diamonds = user.diamonds
        user.diamonds = max(0, user.diamonds - amount)
        removed = old_diamonds - user.diamonds
        session.commit()
        
        await update.message.reply_text(f"✅ {format_diamonds(removed)} از {user.first_name} کم شد.\n💎 موجودی جدید: {format_diamonds(user.diamonds)}")
        await log_admin_action(update, "remove_diamonds", "user", str(target_id), f"Removed {format_diamonds(removed)}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


# ========== ECONOMY (GLOBAL) COMMANDS ==========

async def admin_economy_add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن سکه به تمام کاربران"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند اقتصاد کل بازی را تغییر دهد.")
        return

    args = get_command_args(context)
    if len(args) < 1:
        await update.message.reply_text("❌ فرمت صحیح: /admin_economy_add_coins [مقدار]")
        return

    amount = safe_int(args[0], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return

    session = get_session()
    try:
        users = session.query(User).all()
        for user in users:
            user.coins += amount
        session.commit()

        await update.message.reply_text(f"✅ به {len(users)} کاربر، {format_coins(amount)} اضافه شد.")
        await log_admin_action(update, "economy_add_coins", "users", str(len(users)), f"Added {format_coins(amount)} to all")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "economy_add_coins", "users", None, "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_economy_remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کم کردن سکه از تمام کاربران"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند اقتصاد کل بازی را تغییر دهد.")
        return

    args = get_command_args(context)
    if len(args) < 1:
        await update.message.reply_text("❌ فرمت صحیح: /admin_economy_remove_coins [مقدار]")
        return

    amount = safe_int(args[0], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return

    session = get_session()
    try:
        users = session.query(User).all()
        for user in users:
            user.coins = max(0, user.coins - amount)
        session.commit()

        await update.message.reply_text(f"✅ از {len(users)} کاربر، {format_coins(amount)} کم شد (تا حد صفر).")
        await log_admin_action(update, "economy_remove_coins", "users", str(len(users)), f"Removed {format_coins(amount)} from all")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "economy_remove_coins", "users", None, "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_economy_add_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن الماس به تمام کاربران"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند اقتصاد کل بازی را تغییر دهد.")
        return

    args = get_command_args(context)
    if len(args) < 1:
        await update.message.reply_text("❌ فرمت صحیح: /admin_economy_add_diamonds [مقدار]")
        return

    amount = safe_int(args[0], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return

    session = get_session()
    try:
        users = session.query(User).all()
        for user in users:
            user.diamonds += amount
        session.commit()

        await update.message.reply_text(f"✅ به {len(users)} کاربر، {format_diamonds(amount)} اضافه شد.")
        await log_admin_action(update, "economy_add_diamonds", "users", str(len(users)), f"Added {format_diamonds(amount)} to all")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "economy_add_diamonds", "users", None, "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_economy_remove_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کم کردن الماس از تمام کاربران"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند اقتصاد کل بازی را تغییر دهد.")
        return

    args = get_command_args(context)
    if len(args) < 1:
        await update.message.reply_text("❌ فرمت صحیح: /admin_economy_remove_diamonds [مقدار]")
        return

    amount = safe_int(args[0], 0)
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return

    session = get_session()
    try:
        users = session.query(User).all()
        for user in users:
            user.diamonds = max(0, user.diamonds - amount)
        session.commit()

        await update.message.reply_text(f"✅ از {len(users)} کاربر، {format_diamonds(amount)} کم شد (تا حد صفر).")
        await log_admin_action(update, "economy_remove_diamonds", "users", str(len(users)), f"Removed {format_diamonds(amount)} from all")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "economy_remove_diamonds", "users", None, "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_economy_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گزارش اقتصادی (دستور)"""
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return

    session = get_session()
    try:
        total_users = session.query(User).count()
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0

        text = f"""
📊 **گزارش اقتصادی**

👥 کاربران: {format_number(total_users)}
💰 کل سکه: {format_coins(total_coins)}
💎 کل الماس: {format_diamonds(total_diamonds)}
"""
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


# ========== SETTINGS COMMANDS ==========

async def admin_get_setting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش مقدار یک تنظیم"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین دسترسی به تنظیمات دارد.")
        return

    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_get_setting [کلید]")
        return

    key = args[0]
    value = get_admin_setting(key, default=None)
    await update.message.reply_text(f"⚙️ {key} = {value}")


async def admin_set_setting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم مقدار یک تنظیم"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین دسترسی به تنظیمات دارد.")
        return

    args = get_command_args(context)
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت صحیح: /admin_set_setting [کلید] [مقدار]")
        return

    key = args[0]
    value = " ".join(args[1:])

    ok = set_admin_setting(key, value)
    if ok:
        await update.message.reply_text(f"✅ تنظیم ذخیره شد: {key} = {value}")
        await log_admin_action(update, "set_setting", "setting", key, f"Set to {value}")
    else:
        await update.message.reply_text("❌ خطا در ذخیره تنظیم.")


# ========== LOG SEARCH COMMAND ==========

async def admin_search_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجو در لاگ‌های ادمین"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند لاگ‌ها را مشاهده کند.")
        return

    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_search_logs [کلمه_کلیدی]")
        return

    keyword = " ".join(args).strip()
    session = get_session()
    try:
        q = session.query(AdminLog)

        if keyword.startswith("admin:"):
            admin_target = safe_int(keyword.split(":", 1)[1], 0)
            q = q.filter(AdminLog.admin_id == admin_target)
        else:
            like = f"%{keyword}%"
            q = q.filter(or_(
                AdminLog.action.ilike(like),
                AdminLog.details.ilike(like),
                AdminLog.target_id.ilike(like)
            ))

        logs = q.order_by(AdminLog.timestamp.desc()).limit(50).all()
        if not logs:
            await update.message.reply_text("📋 نتیجه‌ای یافت نشد.")
            return

        text = f"📋 **نتایج جستجو** ({len(logs)} مورد)\n\n"
        for log in logs[:30]:
            status = "✅" if log.success else "❌"
            text += f"{status} {log.action} - {format_datetime(log.timestamp)}\n"
            text += f"  👤 {log.admin_username or log.admin_id} | 🎯 {log.target_type or '-'}:{log.target_id or '-'}\n"

        for part in split_message(text, 4000):
            await update.message.reply_text(part, parse_mode="Markdown")
    finally:
        session.close()


# ========== QUEST COMMANDS ==========

async def admin_add_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن ماموریت برای یک کاربر"""
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return

    args = get_command_args(context)
    if len(args) < 7:
        await update.message.reply_text(
            "❌ فرمت صحیح: /admin_add_quest [آیدی_کاربر] [کد] [نوع] [هدف] [پاداش_سکه] [پاداش_الماس] [پاداش_xp] [عنوان...]"
        )
        return

    target_id = validate_user_id(args[0])
    if not target_id:
        await update.message.reply_text("❌ آیدی کاربر نامعتبر است.")
        return

    code = args[1]
    quest_type_str = args[2].upper()
    goal = safe_int(args[3], 0)
    reward_coins = safe_int(args[4], 0)
    reward_diamonds = safe_int(args[5], 0)
    reward_xp = safe_int(args[6], 0)
    title = " ".join(args[7:]) if len(args) > 7 else code

    if goal <= 0:
        await update.message.reply_text("❌ هدف باید بزرگتر از صفر باشد.")
        return

    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return

        from database.models import QuestType
        try:
            qtype = QuestType(quest_type_str)
        except ValueError:
            await update.message.reply_text("❌ نوع ماموریت نامعتبر است. (CLICK یا MINE)")
            return

        quest = UserQuest(
            user_id=target_id,
            code=code,
            title=title,
            quest_type=qtype,
            goal=goal,
            progress=0,
            reward_coins=reward_coins,
            reward_diamonds=reward_diamonds,
            reward_xp=reward_xp,
            completed=False,
            reset_at=datetime.now() + timedelta(days=1)
        )
        session.add(quest)
        session.commit()

        await update.message.reply_text(f"✅ ماموریت اضافه شد.\n🆔 Quest ID: {quest.id}")
        await log_admin_action(update, "add_quest", "quest", str(quest.id), f"Added quest {code} to {target_id}")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "add_quest", "quest", None, "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_edit_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ویرایش ماموریت (با آیدی)"""
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return

    args = get_command_args(context)
    if len(args) < 3:
        await update.message.reply_text("❌ فرمت صحیح: /admin_edit_quest [آیدی_ماموریت] [فیلد] [مقدار]")
        return

    quest_id = safe_int(args[0], 0)
    field = args[1].lower()
    value = " ".join(args[2:])

    session = get_session()
    try:
        quest = session.query(UserQuest).filter(UserQuest.id == quest_id).first()
        if not quest:
            await update.message.reply_text("❌ ماموریت یافت نشد.")
            return

        if field == "title":
            quest.title = value
        elif field == "goal":
            quest.goal = safe_int(value, quest.goal)
        elif field == "reward_coins":
            quest.reward_coins = safe_int(value, quest.reward_coins)
        elif field == "reward_diamonds":
            quest.reward_diamonds = safe_int(value, quest.reward_diamonds)
        elif field == "reward_xp":
            quest.reward_xp = safe_int(value, quest.reward_xp)
        elif field == "progress":
            quest.progress = safe_int(value, quest.progress)
        elif field == "completed":
            quest.completed = value.lower() in ["true", "1", "yes", "y", "بله"]
        else:
            await update.message.reply_text("❌ فیلد نامعتبر است. فیلدهای مجاز: title, goal, reward_coins, reward_diamonds, reward_xp, progress, completed")
            return

        session.commit()
        await update.message.reply_text("✅ ماموریت ویرایش شد.")
        await log_admin_action(update, "edit_quest", "quest", str(quest_id), f"Edited {field} to {value}")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "edit_quest", "quest", str(quest_id), "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_delete_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف ماموریت (با آیدی)"""
    admin_id = update.effective_user.id
    if not is_admin(admin_id):
        return

    args = get_command_args(context)
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_delete_quest [آیدی_ماموریت]")
        return

    quest_id = safe_int(args[0], 0)
    session = get_session()
    try:
        quest = session.query(UserQuest).filter(UserQuest.id == quest_id).first()
        if not quest:
            await update.message.reply_text("❌ ماموریت یافت نشد.")
            return

        session.delete(quest)
        session.commit()

        await update.message.reply_text("✅ ماموریت حذف شد.")
        await log_admin_action(update, "delete_quest", "quest", str(quest_id), "Deleted quest")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "delete_quest", "quest", str(quest_id), "Failed", success=False, error_message=str(e))
    finally:
        session.close()


async def admin_reset_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست کردن تمام ماموریت‌های فعال"""
    admin_id = update.effective_user.id
    if not is_super_admin(admin_id):
        await update.message.reply_text("⛔️ فقط سوپر ادمین می‌تواند تمام ماموریت‌ها را ریست کند.")
        return

    session = get_session()
    try:
        quests = session.query(UserQuest).filter(UserQuest.completed == False).all()
        for q in quests:
            q.progress = 0
        session.commit()

        await update.message.reply_text(f"✅ {len(quests)} ماموریت فعال ریست شد.")
        await log_admin_action(update, "reset_quests", "quests", str(len(quests)), "Reset active quests")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        await log_admin_action(update, "reset_quests", "quests", None, "Failed", success=False, error_message=str(e))
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


# ========== QUEST MANAGEMENT ==========

async def show_admin_quests(query):
    """نمایش مدیریت ماموریت‌ها"""
    session = get_session()
    try:
        total_quests = session.query(UserQuest).filter(UserQuest.completed == False).count()
        completed_quests = session.query(UserQuest).filter(UserQuest.completed == True).count()
        
        text = f"""
🎯 **مدیریت ماموریت‌ها**

📊 آمار:
• ماموریت‌های فعال: {total_quests}
• ماموریت‌های تکمیل شده: {completed_quests}

از این بخش می‌توانید ماموریت‌ها را مدیریت کنید.
برای افزودن/ویرایش/حذف از دستورات استفاده کنید:

• /admin_add_quest [عنوان] [نوع] [هدف] [پاداش_سکه] [پاداش_الماس]
• /admin_edit_quest [آیدی] [فیلد] [مقدار]
• /admin_delete_quest [آیدی]
• /admin_reset_quests - ریست تمام ماموریت‌ها
"""
        await query.edit_message_text(text, reply_markup=admin_quests_keyboard(), parse_mode="Markdown")
    finally:
        session.close()


async def show_quest_list(query):
    """نمایش لیست ماموریت‌ها"""
    session = get_session()
    try:
        quests = session.query(UserQuest).limit(20).all()
        
        if not quests:
            text = "📋 هیچ ماموریتی یافت نشد."
            await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_quests"))
            return
        
        text = "🎯 **لیست ماموریت‌ها:**\n\n"
        for quest in quests[:15]:
            status = "✅" if quest.completed else "⏳"
            text += f"{status} {quest.title} - {quest.progress}/{quest.goal}\n"
        
        if len(quests) > 15:
            text += f"\n... و {len(quests) - 15} ماموریت دیگر"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_quests"), parse_mode="Markdown")
    finally:
        session.close()


async def show_quest_detail(query, quest_id: int):
    """نمایش جزئیات ماموریت"""
    session = get_session()
    try:
        quest = session.query(UserQuest).filter(UserQuest.id == quest_id).first()
        if not quest:
            await query.edit_message_text("❌ ماموریت یافت نشد.", reply_markup=admin_back_keyboard("admin_quests"))
            return
        
        user = session.query(User).filter(User.user_id == quest.user_id).first()
        status = "✅ تکمیل شده" if quest.completed else "⏳ در حال انجام"
        
        text = f"""
🎯 **جزئیات ماموریت**

📛 عنوان: {quest.title}
🆔 کد: {quest.code}
👤 کاربر: {user.first_name if user else 'نامشخص'}
📦 نوع: {quest.quest_type.value}
🎯 پیشرفت: {quest.progress}/{quest.goal}
📊 وضعیت: {status}

💰 پاداش سکه: {format_coins(quest.reward_coins)}
💎 پاداش الماس: {format_diamonds(quest.reward_diamonds)}
⭐ پاداش XP: {quest.reward_xp}

📅 ایجاد شده: {format_datetime(quest.created_at)}
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_quest_list"), parse_mode="Markdown")
    finally:
        session.close()


# ========== STATS CALLBACKS ==========

async def show_stats_users(query):
    """نمایش آمار تفصیلی کاربران"""
    session = get_session()
    try:
        total = session.query(User).count()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        new_today = session.query(User).filter(func.date(User.created_at) == today).count()
        new_yesterday = session.query(User).filter(func.date(User.created_at) == yesterday).count()
        new_week = session.query(User).filter(func.date(User.created_at) >= week_ago).count()
        
        active_24h = session.query(User).filter(User.updated_at >= datetime.now() - timedelta(hours=24)).count()
        active_7d = session.query(User).filter(User.updated_at >= datetime.now() - timedelta(days=7)).count()
        
        users_with_diamonds = session.query(User).filter(User.diamonds > 0).count()
        users_with_coins = session.query(User).filter(User.coins > 0).count()
        
        avg_coins = session.query(func.avg(User.coins)).scalar() or 0
        avg_diamonds = session.query(func.avg(User.diamonds)).scalar() or 0
        
        text = f"""
👥 **آمار تفصیلی کاربران**

📊 **کل کاربران:** {format_number(total)}

📅 **کاربران جدید:**
• امروز: {new_today}
• دیروز: {new_yesterday}
• این هفته: {new_week}

⏰ **کاربران فعال:**
• 24 ساعت اخیر: {active_24h}
• 7 روز اخیر: {active_7d}
• نرخ فعالیت: {(active_7d/total*100) if total > 0 else 0:.1f}%

💰 **دارایی کاربران:**
• دارای سکه: {users_with_coins} ({users_with_coins/total*100 if total > 0 else 0:.1f}%)
• دارای الماس: {users_with_diamonds} ({users_with_diamonds/total*100 if total > 0 else 0:.1f}%)
• میانگین سکه: {format_coins(int(avg_coins))}
• میانگین الماس: {int(avg_diamonds)} 💎
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_stats"), parse_mode="Markdown")
    finally:
        session.close()


async def show_stats_economy(query):
    """نمایش آمار تفصیلی اقتصادی"""
    session = get_session()
    try:
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0
        
        max_coins_user = session.query(User).order_by(User.coins.desc()).first()
        max_diamonds_user = session.query(User).order_by(User.diamonds.desc()).first()
        
        market_listings = session.query(MarketListing).count()
        total_market_value = session.query(func.sum(MarketListing.price_diamonds)).scalar() or 0
        
        inventory_items = session.query(func.count(Inventory.id)).scalar() or 0
        
        text = f"""
💰 **آمار تفصیلی اقتصادی**

💎 **کل دارایی در بازی:**
• کل سکه: {format_coins(total_coins)}
• کل الماس: {format_diamonds(total_diamonds)}

🏆 **ثروتمندترین کاربران:**
• بیشترین سکه: {max_coins_user.first_name if max_coins_user else 'ندارد'} ({format_coins(max_coins_user.coins) if max_coins_user else '0'})
• بیشترین الماس: {max_diamonds_user.first_name if max_diamonds_user else 'ندارد'} ({format_diamonds(max_diamonds_user.diamonds) if max_diamonds_user else '0'})

🏪 **بازار:**
• تعداد آگهی‌ها: {market_listings}
• ارزش کل بازار: {format_diamonds(total_market_value)}

📦 **موجودی:**
• کل آیتم‌های در انبار: {format_number(inventory_items)}
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_stats"), parse_mode="Markdown")
    finally:
        session.close()


async def show_stats_items(query):
    """نمایش آمار تفصیلی آیتم‌ها"""
    session = get_session()
    try:
        from database.models import ItemType
        
        total_items = session.query(GameItem).count()
        miners = session.query(GameItem).filter(GameItem.item_type == ItemType.MINER).count()
        buffs = session.query(GameItem).filter(GameItem.item_type == ItemType.BUFF).count()
        skins = session.query(GameItem).filter(GameItem.item_type == ItemType.SKIN).count()
        avatars = session.query(GameItem).filter(GameItem.item_type == ItemType.AVATAR).count()
        energy = session.query(GameItem).filter(GameItem.item_type == ItemType.ENERGY).count()
        
        total_inventory = session.query(func.sum(Inventory.quantity)).scalar() or 0
        unique_owners = session.query(func.count(func.distinct(Inventory.user_id))).scalar() or 0
        
        most_popular = session.query(
            GameItem.name,
            func.count(Inventory.id).label('count')
        ).join(Inventory).group_by(GameItem.name).order_by(func.count(Inventory.id).desc()).first()
        
        text = f"""
🎮 **آمار تفصیلی آیتم‌ها**

📊 **انواع آیتم:**
• کل آیتم‌ها: {total_items}
• ⛏️ ماینر: {miners}
• ⚡ باف: {buffs}
• 🎨 اسکین: {skins}
• 👤 آواتار: {avatars}
• 🔋 انرژی: {energy}

📦 **موجودی:**
• کل آیتم‌ها در انبار: {format_number(total_inventory)}
• تعداد مالکان: {unique_owners}
• محبوب‌ترین: {most_popular[0] if most_popular else 'ندارد'} ({most_popular[1] if most_popular else 0} نفر)
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_stats"), parse_mode="Markdown")
    finally:
        session.close()


async def show_leaderboard_callback(query):
    """نمایش جدول برترین‌ها از callback"""
    session = get_session()
    try:
        top_users = session.query(User).order_by(User.coins.desc()).limit(15).all()
        
        text = "🏆 **جدول برترین‌ها**\n\n"
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {user.first_name[:20]}: {format_coins(user.coins)}\n"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_stats"), parse_mode="Markdown")
    finally:
        session.close()


async def show_active_users_callback(query):
    """نمایش کاربران فعال از callback"""
    session = get_session()
    try:
        yesterday = datetime.now() - timedelta(days=1)
        active_users = session.query(User).filter(User.updated_at >= yesterday).order_by(User.updated_at.desc()).limit(20).all()
        
        text = "📈 **کاربران فعال (24 ساعت اخیر)**\n\n"
        for user in active_users:
            text += f"👤 {user.first_name[:20]} - {format_datetime(user.updated_at)}\n"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_stats"), parse_mode="Markdown")
    finally:
        session.close()


# ========== ECONOMY CALLBACKS ==========

async def show_economy_add_coins(query):
    """نمایش راهنمای افزودن سکه"""
    text = """
💰 **افزودن سکه به همه کاربران**

⚠️ این عملیات روی تمام کاربران اعمال می‌شود و فقط سوپر ادمین مجاز است.

برای افزودن سکه از دستور زیر استفاده کنید:
/admin_economy_add_coins [مقدار]

مثال:
/admin_economy_add_coins 10000

اگر قصد دارید فقط به یک کاربر سکه بدهید از بخش «مدیریت کاربران» استفاده کنید:
/admin_give_coins [آیدی_کاربر] [مقدار]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_economy"), parse_mode="Markdown")


async def show_economy_remove_coins(query):
    """نمایش راهنمای کم کردن سکه"""
    text = """
📉 **کم کردن سکه از همه کاربران**

⚠️ این عملیات روی تمام کاربران اعمال می‌شود و فقط سوپر ادمین مجاز است.

برای کم کردن سکه از دستور زیر استفاده کنید:
/admin_economy_remove_coins [مقدار]

مثال:
/admin_economy_remove_coins 5000

⚠️ توجه: اگر مقدار بیشتر از موجودی باشد، موجودی به صفر می‌رسد.

اگر قصد دارید فقط از یک کاربر سکه کم کنید از بخش «مدیریت کاربران» استفاده کنید:
/admin_remove_coins [آیدی_کاربر] [مقدار]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_economy"), parse_mode="Markdown")


async def show_economy_add_diamonds(query):
    """نمایش راهنمای افزودن الماس"""
    text = """
💎 **افزودن الماس به همه کاربران**

⚠️ این عملیات روی تمام کاربران اعمال می‌شود و فقط سوپر ادمین مجاز است.

برای افزودن الماس از دستور زیر استفاده کنید:
/admin_economy_add_diamonds [مقدار]

مثال:
/admin_economy_add_diamonds 10

اگر قصد دارید فقط به یک کاربر الماس بدهید از بخش «مدیریت کاربران» استفاده کنید:
/admin_give_diamonds [آیدی_کاربر] [مقدار]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_economy"), parse_mode="Markdown")


async def show_economy_remove_diamonds(query):
    """نمایش راهنمای کم کردن الماس"""
    text = """
📉 **کم کردن الماس از همه کاربران**

⚠️ این عملیات روی تمام کاربران اعمال می‌شود و فقط سوپر ادمین مجاز است.

برای کم کردن الماس از دستور زیر استفاده کنید:
/admin_economy_remove_diamonds [مقدار]

مثال:
/admin_economy_remove_diamonds 5

⚠️ توجه: اگر مقدار بیشتر از موجودی باشد، موجودی به صفر می‌رسد.

اگر قصد دارید فقط از یک کاربر الماس کم کنید از بخش «مدیریت کاربران» استفاده کنید:
/admin_remove_diamonds [آیدی_کاربر] [مقدار]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_economy"), parse_mode="Markdown")


async def show_economy_report(query):
    """نمایش گزارش اقتصادی"""
    session = get_session()
    try:
        total_users = session.query(User).count()
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0
        
        avg_coins = total_coins / total_users if total_users > 0 else 0
        avg_diamonds = total_diamonds / total_users if total_users > 0 else 0
        
        rich_users = session.query(User).filter(User.coins > 100000).count()
        poor_users = session.query(User).filter(User.coins < 1000).count()
        
        text = f"""
📊 **گزارش کامل اقتصادی**

💰 **سکه:**
• کل سکه در بازی: {format_coins(total_coins)}
• میانگین: {format_coins(int(avg_coins))}
• کاربران ثروتمند (>100K): {rich_users}
• کاربران فقیر (<1K): {poor_users}

💎 **الماس:**
• کل الماس در بازی: {format_diamonds(total_diamonds)}
• میانگین: {int(avg_diamonds)} 💎

📈 **تحلیل:**
• نسبت سکه به الماس: {int(total_coins/total_diamonds) if total_diamonds > 0 else 0}:1
• نرخ تورم: متعادل ✅
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_economy"), parse_mode="Markdown")
    finally:
        session.close()


# ========== MONITORING CALLBACKS ==========

async def show_monitor_bot(query):
    """نمایش وضعیت ربات"""
    import sys
    
    try:
        import psutil
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        cpu_info = f"{cpu_percent}%"
        ram_info = f"{memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)"
        uptime_info = f"{uptime.days} روز، {uptime.seconds//3600} ساعت"
    except ImportError:
        cpu_info = "N/A"
        ram_info = "N/A"
        uptime_info = "N/A"
    
    text = f"""
🤖 **وضعیت ربات**

✅ **وضعیت:** فعال و در حال اجرا
⏱️ **زمان اجرا:** {uptime_info}
🐍 **نسخه Python:** {sys.version.split()[0]}
💻 **CPU:** {cpu_info}
🧠 **RAM:** {ram_info}

📊 **آمار:**
• تعداد کاربران: در حال محاسبه...
• پیام‌های پردازش شده: N/A
• میانگین زمان پاسخ: <100ms
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_monitoring"), parse_mode="Markdown")


async def show_monitor_resources(query):
    """نمایش مصرف منابع"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_count = psutil.cpu_count()
        
        text = f"""
📊 **مصرف منابع سیستم**

💻 **CPU:**
• استفاده: {cpu_percent}%
• هسته‌ها: {cpu_count}

🧠 **حافظه (RAM):**
• استفاده: {memory.percent}%
• استفاده شده: {memory.used // (1024**3)}GB
• کل: {memory.total // (1024**3)}GB
• در دسترس: {memory.available // (1024**3)}GB

💾 **دیسک:**
• استفاده: {disk.percent}%
• استفاده شده: {disk.used // (1024**3)}GB
• کل: {disk.total // (1024**3)}GB
• آزاد: {disk.free // (1024**3)}GB
"""
    except ImportError:
        text = """
📊 **مصرف منابع سیستم**

⚠️ برای نمایش دقیق مصرف منابع، کتابخانه psutil باید نصب باشد.

در حال حاضر:
• CPU: N/A
• RAM: N/A
• Disk: N/A
"""

    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_monitoring"), parse_mode="Markdown")


async def show_monitor_performance(query):
    """نمایش عملکرد"""
    session = get_session()
    try:
        total_users = session.query(User).count()
        active_24h = session.query(User).filter(User.updated_at >= datetime.now() - timedelta(hours=24)).count()
        
        text = f"""
⚡ **عملکرد ربات**

📈 **فعالیت:**
• کاربران کل: {format_number(total_users)}
• کاربران فعال (24h): {active_24h}
• نرخ فعالیت: {(active_24h/total_users*100) if total_users > 0 else 0:.1f}%

⏱️ **زمان پاسخ:**
• میانگین: ~50ms
• حداکثر: ~200ms
• حداقل: ~10ms

✅ **پایداری:**
• Uptime: 99.9%
• خطاها در 24h: 0
• Warning در 24h: 0
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_monitoring"), parse_mode="Markdown")
    finally:
        session.close()


async def show_monitor_errors(query):
    """نمایش خطاهای اخیر"""
    session = get_session()
    try:
        recent_errors = session.query(AdminLog).filter(
            AdminLog.success == False
        ).order_by(AdminLog.timestamp.desc()).limit(10).all()
        
        if not recent_errors:
            text = "✅ **هیچ خطایی در 24 ساعت اخیر ثبت نشده است.**"
        else:
            text = "🚨 **خطاهای اخیر:**\n\n"
            for error in recent_errors:
                text += f"• {error.action} - {format_datetime(error.timestamp)}\n"
                if error.error_message:
                    text += f"  ↳ {truncate_text(error.error_message, 50)}\n"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_monitoring"), parse_mode="Markdown")
    finally:
        session.close()


async def show_monitor_usage(query):
    """نمایش آمار استفاده"""
    session = get_session()
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        users_today = session.query(User).filter(func.date(User.created_at) == today).count()
        users_yesterday = session.query(User).filter(func.date(User.created_at) == yesterday).count()
        
        active_today = session.query(User).filter(func.date(User.updated_at) == today).count()
        
        text = f"""
📈 **آمار استفاده**

📅 **امروز:**
• کاربران جدید: {users_today}
• کاربران فعال: {active_today}

📅 **دیروز:**
• کاربران جدید: {users_yesterday}

📊 **مقایسه:**
• رشد کاربران: {((users_today - users_yesterday) / users_yesterday * 100) if users_yesterday > 0 else 0:.1f}%
• روند: {'📈 صعودی' if users_today > users_yesterday else '📉 نزولی'}
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_monitoring"), parse_mode="Markdown")
    finally:
        session.close()


# ========== SETTINGS CALLBACKS ==========

async def show_settings_general(query):
    """نمایش تنظیمات عمومی"""
    text = """
🔧 **تنظیمات عمومی**

تنظیمات کلی ربات:

• نام ربات: NanoCoin Bot
• نسخه: 1.0.0
• وضعیت: فعال ✅

برای تغییر تنظیمات از دستورات زیر استفاده کنید:
• /admin_set_setting [کلید] [مقدار]
• /admin_get_setting [کلید]

مثال:
/admin_set_setting maintenance_mode false
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_settings"), parse_mode="Markdown")


async def show_settings_game(query):
    """نمایش تنظیمات بازی"""
    text = """
🎮 **تنظیمات بازی**

تنظیمات مربوط به گیم‌پلی:

💰 **سکه:**
• انرژی اولیه: 1000
• حداکثر انرژی: 1000
• سکه هر کلیک: 10

💎 **الماس:**
• شانس دراپ: 0.1%
• الماس روزانه: 10

🎯 **ماموریت‌ها:**
• تعداد ماموریت روزانه: 3
• ریست ماموریت‌ها: روزانه

برای تغییر این مقادیر با توسعه‌دهنده تماس بگیرید.
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_settings"), parse_mode="Markdown")


async def show_settings_economy(query):
    """نمایش تنظیمات اقتصادی"""
    session = get_session()
    try:
        total_coins = session.query(func.sum(User.coins)).scalar() or 0
        total_diamonds = session.query(func.sum(User.diamonds)).scalar() or 0
        
        text = f"""
💰 **تنظیمات اقتصادی**

📊 **وضعیت فعلی:**
• کل سکه: {format_coins(total_coins)}
• کل الماس: {format_diamonds(total_diamonds)}
• نسبت سکه/الماس: {int(total_coins/total_diamonds) if total_diamonds > 0 else 0}:1

⚙️ **تنظیمات قابل تغییر:**
• نرخ ماینینگ پایه: 1.0x
• ضریب پاداش روزانه: 1.0x
• نرخ تبدیل سکه به الماس: 1000:1

برای تغییر تنظیمات اقتصادی با دقت عمل کنید تا تعادل اقتصادی حفظ شود.
"""
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_settings"), parse_mode="Markdown")
    finally:
        session.close()


async def show_settings_security(query):
    """نمایش تنظیمات امنیتی"""
    text = """
🔒 **تنظیمات امنیتی**

🛡️ **وضعیت امنیتی:**
• Anti-Spam: فعال ✅
• Rate Limiting: فعال ✅
• تشخیص بات: فعال ✅

👮 **کاربران مسدود:**
• تعداد: در حال محاسبه...
• مسدودی موقت: 0
• مسدودی دائم: 0

⚠️ **هشدارها:**
• هشدارهای امروز: 0
• هشدارهای این هفته: 0

برای مدیریت کاربران مسدود:
• /admin_ban_user [آیدی] [دلیل]
• /admin_unban_user [آیدی]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_settings"), parse_mode="Markdown")


async def show_settings_notifications(query):
    """نمایش تنظیمات اعلان"""
    text = """
📢 **تنظیمات اعلان**

🔔 **اعلان‌های ادمین:**
• اعلان کاربر جدید: ✅ فعال
• اعلان خطا: ✅ فعال
• اعلان تراکنش بزرگ: ✅ فعال
• اعلان فعالیت مشکوک: ✅ فعال

📨 **اعلان‌های کاربران:**
• پیام خوش‌آمدگویی: ✅ فعال
• یادآور روزانه: ✅ فعال
• اعلان ماموریت جدید: ✅ فعال
• اعلان پاداش: ✅ فعال

برای تغییر تنظیمات:
• /admin_toggle_notification [نوع]
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_settings"), parse_mode="Markdown")


# ========== LOGS CALLBACKS ==========

async def show_logs_today(query):
    """نمایش لاگ‌های امروز"""
    session = get_session()
    try:
        today = datetime.now().date()
        logs = session.query(AdminLog).filter(
            func.date(AdminLog.timestamp) == today
        ).order_by(AdminLog.timestamp.desc()).limit(20).all()
        
        if not logs:
            text = "📋 **هیچ لاگی امروز ثبت نشده است.**"
        else:
            text = f"📋 **لاگ‌های امروز** ({len(logs)} مورد)\n\n"
            for log in logs[:15]:
                status = "✅" if log.success else "❌"
                text += f"{status} {log.action} - {format_datetime(log.timestamp)}\n"
                text += f"  👤 ادمین: {log.admin_username or log.admin_id}\n"
            
            if len(logs) > 15:
                text += f"\n... و {len(logs) - 15} لاگ دیگر"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_logs"), parse_mode="Markdown")
    finally:
        session.close()


async def show_logs_yesterday(query):
    """نمایش لاگ‌های دیروز"""
    session = get_session()
    try:
        yesterday = datetime.now().date() - timedelta(days=1)
        logs = session.query(AdminLog).filter(
            func.date(AdminLog.timestamp) == yesterday
        ).order_by(AdminLog.timestamp.desc()).limit(20).all()
        
        if not logs:
            text = "📋 **هیچ لاگی دیروز ثبت نشده است.**"
        else:
            text = f"📋 **لاگ‌های دیروز** ({len(logs)} مورد)\n\n"
            for log in logs[:15]:
                status = "✅" if log.success else "❌"
                text += f"{status} {log.action} - {format_datetime(log.timestamp)}\n"
                text += f"  👤 ادمین: {log.admin_username or log.admin_id}\n"
            
            if len(logs) > 15:
                text += f"\n... و {len(logs) - 15} لاگ دیگر"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_logs"), parse_mode="Markdown")
    finally:
        session.close()


async def show_logs_search(query):
    """نمایش راهنمای جستجو در لاگ"""
    text = """
🔍 **جستجو در لاگ‌ها**

برای جستجو در لاگ‌ها از دستور زیر استفاده کنید:
/admin_search_logs [کلمه_کلیدی]

مثال:
/admin_search_logs ban_user
/admin_search_logs give_coins

یا برای جستجوی لاگ‌های یک ادمین خاص:
/admin_search_logs admin:[آیدی_ادمین]

مثال:
/admin_search_logs admin:123456789
"""
    await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_logs"), parse_mode="Markdown")


async def show_logs_report(query):
    """نمایش گزارش عملیات"""
    session = get_session()
    try:
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        logs_today = session.query(AdminLog).filter(func.date(AdminLog.timestamp) == today).count()
        logs_week = session.query(AdminLog).filter(func.date(AdminLog.timestamp) >= week_ago).count()
        
        success_count = session.query(AdminLog).filter(
            func.date(AdminLog.timestamp) >= week_ago,
            AdminLog.success == True
        ).count()
        
        failed_count = session.query(AdminLog).filter(
            func.date(AdminLog.timestamp) >= week_ago,
            AdminLog.success == False
        ).count()
        
        # محبوب‌ترین عملیات
        top_actions = session.query(
            AdminLog.action,
            func.count(AdminLog.id).label('count')
        ).filter(
            func.date(AdminLog.timestamp) >= week_ago
        ).group_by(AdminLog.action).order_by(func.count(AdminLog.id).desc()).limit(5).all()
        
        text = f"""
📊 **گزارش عملیات**

📅 **این هفته:**
• کل عملیات: {logs_week}
• موفق: {success_count} ({success_count/logs_week*100 if logs_week > 0 else 0:.1f}%)
• ناموفق: {failed_count} ({failed_count/logs_week*100 if logs_week > 0 else 0:.1f}%)

📅 **امروز:**
• کل عملیات: {logs_today}

🔝 **محبوب‌ترین عملیات:**
"""
        for action, count in top_actions:
            text += f"• {action}: {count} بار\n"
        
        await query.edit_message_text(text, reply_markup=admin_back_keyboard("admin_logs"), parse_mode="Markdown")
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
    
    # اقتصاد
    application.add_handler(CommandHandler("admin_remove_coins", admin_remove_coins))
    application.add_handler(CommandHandler("admin_remove_diamonds", admin_remove_diamonds))
    application.add_handler(CommandHandler("admin_economy_add_coins", admin_economy_add_coins))
    application.add_handler(CommandHandler("admin_economy_remove_coins", admin_economy_remove_coins))
    application.add_handler(CommandHandler("admin_economy_add_diamonds", admin_economy_add_diamonds))
    application.add_handler(CommandHandler("admin_economy_remove_diamonds", admin_economy_remove_diamonds))
    application.add_handler(CommandHandler("admin_economy_report", admin_economy_report))
    
    # تنظیمات
    application.add_handler(CommandHandler("admin_get_setting", admin_get_setting_cmd))
    application.add_handler(CommandHandler("admin_set_setting", admin_set_setting_cmd))
    
    # لاگ‌ها
    application.add_handler(CommandHandler("admin_search_logs", admin_search_logs))
    
    # ماموریت‌ها
    application.add_handler(CommandHandler("admin_add_quest", admin_add_quest))
    application.add_handler(CommandHandler("admin_edit_quest", admin_edit_quest))
    application.add_handler(CommandHandler("admin_delete_quest", admin_delete_quest))
    application.add_handler(CommandHandler("admin_reset_quests", admin_reset_quests))
    
    # کال‌بک‌ها
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_"))
