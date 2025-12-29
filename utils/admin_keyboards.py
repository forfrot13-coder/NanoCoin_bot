from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from database.admin_models import JoinRequirement
from database.connection import get_session


def admin_main_keyboard():
    """کیبورد اصلی پنل ادمین"""
    keyboard = [
        [InlineKeyboardButton("📊 آمار و تحلیل", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("🎮 مدیریت آیتم‌ها", callback_data="admin_items")],
        [InlineKeyboardButton("🎯 مدیریت ماموریت‌ها", callback_data="admin_quests")],
        [InlineKeyboardButton("💎 الماس و سکه", callback_data="admin_economy")],
        [InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔗 مدیریت جوین", callback_data="admin_join")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")],
        [InlineKeyboardButton("🔍 نظارت بر سیستم", callback_data="admin_monitoring")],
        [InlineKeyboardButton("📋 لاگ‌ها", callback_data="admin_logs")],
        [InlineKeyboardButton("❌ خروج", callback_data="admin_exit")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_back_keyboard(callback_data: str = "admin_main"):
    """کیبورد بازگشت"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]
    ])


def admin_cancel_keyboard():
    """کیبورد انصراف"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_cancel")]
    ])


def admin_stats_keyboard():
    """کیبورد آمار و تحلیل"""
    keyboard = [
        [InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_stats_users")],
        [InlineKeyboardButton("💰 آمار اقتصادی", callback_data="admin_stats_economy")],
        [InlineKeyboardButton("🎮 آمار آیتم‌ها", callback_data="admin_stats_items")],
        [InlineKeyboardButton("🏆 جدول برترین‌ها", callback_data="admin_leaderboard")],
        [InlineKeyboardButton("📈 کاربران فعال", callback_data="admin_active_users")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_users_keyboard():
    """کیبورد مدیریت کاربران"""
    keyboard = [
        [InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_user_search")],
        [InlineKeyboardButton("📋 لیست کاربران", callback_data="admin_user_list")],
        [InlineKeyboardButton("🚫 مسدود کردن", callback_data="admin_user_ban")],
        [InlineKeyboardButton("✅ رفع مسدودی", callback_data="admin_user_unban")],
        [InlineKeyboardButton("💰 دادن سکه/الماس", callback_data="admin_user_give")],
        [InlineKeyboardButton("🔄 ریست کاربر", callback_data="admin_user_reset")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_items_keyboard():
    """کیبورد مدیریت آیتم‌ها"""
    keyboard = [
        [InlineKeyboardButton("➕ اضافه کردن آیتم", callback_data="admin_item_add")],
        [InlineKeyboardButton("✏️ ویرایش آیتم", callback_data="admin_item_edit")],
        [InlineKeyboardButton("🗑 حذف آیتم", callback_data="admin_item_delete")],
        [InlineKeyboardButton("💎 تنظیم قیمت", callback_data="admin_item_price")],
        [InlineKeyboardButton("📊 موجودی انبار", callback_data="admin_item_stock")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_quests_keyboard():
    """کیبورد مدیریت ماموریت‌ها"""
    keyboard = [
        [InlineKeyboardButton("➕ اضافه کردن ماموریت", callback_data="admin_quest_add")],
        [InlineKeyboardButton("✏️ ویرایش ماموریت", callback_data="admin_quest_edit")],
        [InlineKeyboardButton("🗑 حذف ماموریت", callback_data="admin_quest_delete")],
        [InlineKeyboardButton("📋 لیست ماموریت‌ها", callback_data="admin_quest_list")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_economy_keyboard():
    """کیبورد مدیریت اقتصاد"""
    keyboard = [
        [InlineKeyboardButton("💰 اضافه سکه", callback_data="admin_economy_add_coins")],
        [InlineKeyboardButton("💎 اضافه الماس", callback_data="admin_economy_add_diamonds")],
        [InlineKeyboardButton("📉 کم کردن سکه", callback_data="admin_economy_remove_coins")],
        [InlineKeyboardButton("📉 کم کردن الماس", callback_data="admin_economy_remove_diamonds")],
        [InlineKeyboardButton("📊 گزارش اقتصادی", callback_data="admin_economy_report")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_broadcast_keyboard():
    """کیبورد ارسال همگانی"""
    keyboard = [
        [InlineKeyboardButton("📝 ارسال پیام متنی", callback_data="admin_broadcast_text")],
        [InlineKeyboardButton("🖼 ارسال عکس", callback_data="admin_broadcast_photo")],
        [InlineKeyboardButton("📊 ارسال نظرسنجی", callback_data="admin_broadcast_poll")],
        [InlineKeyboardButton("⏰ ارسال زمان‌بندی", callback_data="admin_broadcast_scheduled")],
        [InlineKeyboardButton("📈 وضعیت ارسال‌ها", callback_data="admin_broadcast_status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_join_keyboard():
    """کیبورد مدیریت جوین"""
    keyboard = [
        [InlineKeyboardButton("➕ اضافه کردن گروه/کانال", callback_data="admin_join_add")],
        [InlineKeyboardButton("➖ حذف کردن گروه/کانال", callback_data="admin_join_remove")],
        [InlineKeyboardButton("📋 لیست الزامات جوین", callback_data="admin_join_list")],
        [InlineKeyboardButton("✏️ ویرایش پیام", callback_data="admin_join_edit_message")],
        [InlineKeyboardButton("✅ فعال/غیرفعال", callback_data="admin_join_toggle")],
        [InlineKeyboardButton("🔄 بررسی وضعیت", callback_data="admin_join_check")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_join_list_keyboard(requirements: list):
    """کیبورد لیست الزامات جوین"""
    keyboard = []
    for req in requirements:
        status = "✅" if req.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {req.chat_name[:20]}", 
                callback_data=f"admin_join_view_{req.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")])
    return InlineKeyboardMarkup(keyboard)


def admin_join_detail_keyboard(req_id: int, is_active: bool):
    """کیبورد جزئیات جوین"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ ویرایش پیام", callback_data=f"admin_join_edit_{req_id}"),
            InlineKeyboardButton("🔗 لینک دعوت", callback_data=f"admin_join_link_{req_id}"),
        ],
        [
            InlineKeyboardButton("✅ فعال", callback_data=f"admin_join_activate_{req_id}") if not is_active else InlineKeyboardButton("❌ غیرفعال", callback_data=f"admin_join_deactivate_{req_id}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"admin_join_delete_{req_id}"),
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_settings_keyboard():
    """کیبورد تنظیمات"""
    keyboard = [
        [InlineKeyboardButton("🔧 تنظیمات عمومی", callback_data="admin_settings_general")],
        [InlineKeyboardButton("🎮 تنظیمات بازی", callback_data="admin_settings_game")],
        [InlineKeyboardButton("💰 تنظیمات اقتصادی", callback_data="admin_settings_economy")],
        [InlineKeyboardButton("🔒 تنظیمات امنیتی", callback_data="admin_settings_security")],
        [InlineKeyboardButton("📢 تنظیمات اعلان", callback_data="admin_settings_notifications")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_monitoring_keyboard():
    """کیبورد نظارت بر سیستم"""
    keyboard = [
        [InlineKeyboardButton("🤖 وضعیت ربات", callback_data="admin_monitor_bot")],
        [InlineKeyboardButton("📊 مصرف منابع", callback_data="admin_monitor_resources")],
        [InlineKeyboardButton("⚡ عملکرد", callback_data="admin_monitor_performance")],
        [InlineKeyboardButton("🚨 خطاهای اخیر", callback_data="admin_monitor_errors")],
        [InlineKeyboardButton("📈 آمار استفاده", callback_data="admin_monitor_usage")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_logs_keyboard():
    """کیبورد لاگ‌ها"""
    keyboard = [
        [InlineKeyboardButton("📋 لاگ امروز", callback_data="admin_logs_today")],
        [InlineKeyboardButton("📋 لاگ دیروز", callback_data="admin_logs_yesterday")],
        [InlineKeyboardButton("🔍 جستجو در لاگ", callback_data="admin_logs_search")],
        [InlineKeyboardButton("📊 گزارش عملیات", callback_data="admin_logs_report")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_user_list_keyboard(users: list, page: int = 1, total_pages: int = 1):
    """کیبورد لیست کاربران"""
    keyboard = []
    for user in users:
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {user.first_name[:15]}", 
                callback_data=f"admin_user_view_{user.user_id}"
            )
        ])
    
    # دکمه‌های صفحه‌بندی
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"admin_users_page_{page-1}"))
    pagination.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="admin_users_page_current"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton("▶️ بعدی", callback_data=f"admin_users_page_{page+1}"))
    keyboard.append(pagination)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users")])
    return InlineKeyboardMarkup(keyboard)


def admin_user_detail_keyboard(user_id: int):
    """کیبورد جزئیات کاربر"""
    keyboard = [
        [InlineKeyboardButton("💰 دادن سکه", callback_data=f"admin_user_give_coins_{user_id}"),
         InlineKeyboardButton("💎 دادن الماس", callback_data=f"admin_user_give_diamonds_{user_id}")],
        [InlineKeyboardButton("⚡ انرژی", callback_data=f"admin_user_energy_{user_id}"),
         InlineKeyboardButton("📊 سطح", callback_data=f"admin_user_level_{user_id}")],
        [InlineKeyboardButton("🚫 مسدود کردن", callback_data=f"admin_user_ban_{user_id}"),
         InlineKeyboardButton("🔓 رفع مسدودی", callback_data=f"admin_user_unban_{user_id}")],
        [InlineKeyboardButton("🔄 ریست کاربر", callback_data=f"admin_user_reset_{user_id}"),
         InlineKeyboardButton("🗑 حذف کاربر", callback_data=f"admin_user_delete_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_user_list")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_confirm_keyboard(action: str, target_id: str):
    """کیبورد تایید عملیات"""
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"admin_confirm_{action}_{target_id}"),
            InlineKeyboardButton("❌ لغو", callback_data="admin_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_item_list_keyboard(items: list, page: int = 1, total_pages: int = 1):
    """کیبورد لیست آیتم‌ها"""
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"{item.emoji} {item.name[:15]}", 
                callback_data=f"admin_item_view_{item.id}"
            )
        ])
    
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"admin_items_page_{page-1}"))
    pagination.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="admin_items_page_current"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton("▶️ بعدی", callback_data=f"admin_items_page_{page+1}"))
    keyboard.append(pagination)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_items")])
    return InlineKeyboardMarkup(keyboard)


def admin_item_detail_keyboard(item_id: int):
    """کیبورد جزئیات آیتم"""
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_item_edit_{item_id}"),
         InlineKeyboardButton("💎 قیمت", callback_data=f"admin_item_price_{item_id}")],
        [InlineKeyboardButton("📦 موجودی", callback_data=f"admin_item_stock_{item_id}"),
         InlineKeyboardButton("🔄 فعال/غیرفعال", callback_data=f"admin_item_toggle_{item_id}")],
        [InlineKeyboardButton("🗑 حذف", callback_data=f"admin_item_delete_{item_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_items")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_broadcast_confirm_keyboard(broadcast_id: int):
    """کیبورد تایید ارسال همگانی"""
    keyboard = [
        [
            InlineKeyboardButton("✅ ارسال همگانی", callback_data=f"admin_broadcast_send_{broadcast_id}"),
            InlineKeyboardButton("❌ لغو", callback_data="admin_broadcast"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def verification_keyboard(invite_link: str = None):
    """کیبورد تایید جوین"""
    keyboard = []
    if invite_link:
        keyboard.append([InlineKeyboardButton("🔗 جوین در گروه", url=invite_link)])
    keyboard.append([InlineKeyboardButton("🔄 بررسی مجدد", callback_data="verify_join")])
    return InlineKeyboardMarkup(keyboard)


def admin_help_keyboard():
    """کیبورد راهنمای ادمین"""
    keyboard = [
        [InlineKeyboardButton("📖 تعریف بخش‌ها", callback_data="admin_help_section_definition")],
        [InlineKeyboardButton("⌨️ دستورات اصلی", callback_data="admin_help_section_commands")],
        [InlineKeyboardButton("🔗 مدیریت جوین", callback_data="admin_help_section_join")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_help_section_users")],
        [InlineKeyboardButton("🎮 مدیریت آیتم‌ها", callback_data="admin_help_section_items")],
        [InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin_help_section_broadcast")],
        [InlineKeyboardButton("❓ سوالات متداول", callback_data="admin_help_section_faq")],
        [InlineKeyboardButton("🚨 اضطراری", callback_data="admin_help_section_emergency")],
        [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_inline_yes_nokeyboard(callback_prefix: str):
    """کیبورد بله/خیر"""
    keyboard = [
        [
            InlineKeyboardButton("✅ بله", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("❌ خیر", callback_data=f"{callback_prefix}_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
