import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update
from database.connection import get_session
from database.admin_models import AdminLog, AdminSettings
from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """بررسی می‌کند که آیا کاربر ادمین است"""
    return user_id in ADMIN_IDS


def is_super_admin(user_id: int) -> bool:
    """بررسی می‌کند که آیا کاربر سوپر ادمین است (اولین ادمین)"""
    return len(ADMIN_IDS) > 0 and user_id == ADMIN_IDS[0]


def get_admin_level(user_id: int) -> int:
    """دریافت سطح دسترسی ادمین
    0: ادمین نیست
    1: ادمین معمولی
    2: سوپر ادمین
    """
    if user_id not in ADMIN_IDS:
        return 0
    if user_id == ADMIN_IDS[0]:
        return 2
    return 1


async def log_admin_action(
    update: Update,
    action: str,
    target_type: str = None,
    target_id: str = None,
    details: str = None,
    success: bool = True,
    error_message: str = None
):
    """ثبت عملیات ادمین در لاگ"""
    try:
        session = get_session()
        log = AdminLog(
            admin_id=update.effective_user.id,
            admin_username=update.effective_user.username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            success=success,
            error_message=error_message
        )
        session.add(log)
        session.commit()
        session.close()
        logger.info(f"Admin action logged: {action} by {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


def get_admin_setting(key: str, default: Any = None) -> Any:
    """دریافت مقدار یک تنظیم ادمین"""
    session = get_session()
    try:
        setting = session.query(AdminSettings).filter(AdminSettings.setting_key == key).first()
        if setting:
            if setting.setting_type == 'int':
                return int(setting.setting_value)
            elif setting.setting_type == 'bool':
                return setting.setting_value.lower() == 'true'
            elif setting.setting_type == 'json':
                return json.loads(setting.setting_value)
            return setting.setting_value
        return default
    except Exception as e:
        logger.error(f"Error getting admin setting {key}: {e}")
        return default
    finally:
        session.close()


def set_admin_setting(key: str, value: Any, setting_type: str = 'string', description: str = None):
    """تنظیم مقدار یک تنظیم ادمین"""
    session = get_session()
    try:
        setting = session.query(AdminSettings).filter(AdminSettings.setting_key == key).first()
        str_value = str(value)
        
        if setting:
            setting.setting_value = str_value
            setting.setting_type = setting_type
            if description:
                setting.description = description
        else:
            setting = AdminSettings(
                setting_key=key,
                setting_value=str_value,
                setting_type=setting_type,
                description=description
            )
            session.add(setting)
        
        session.commit()
        logger.info(f"Admin setting updated: {key} = {value}")
        return True
    except Exception as e:
        logger.error(f"Error setting admin setting {key}: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def format_number(num: int) -> str:
    """فرمت کردن اعداد بزرگ"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_coins(num: int) -> str:
    """فرمت کردن سکه"""
    return f"{format_number(num)} 🪙"


def format_diamonds(num: int) -> str:
    """فرمت کردن الماس"""
    return f"{format_number(num)} 💎"


def get_user_display_name(user_id: int, first_name: str = None, username: str = None) -> str:
    """دریافت نام نمایشی کاربر"""
    if first_name:
        return first_name
    if username:
        return f"@{username}"
    return f"کاربر {user_id}"


def format_datetime(dt: datetime) -> str:
    """فرمت کردن تاریخ و زمان"""
    return dt.strftime("%Y/%m/%d - %H:%M")


def parse_duration(duration_str: str) -> Optional[int]:
    """تبدیل رشته مدت زمان به ثانیه
    پشتیبانی از: 1h, 30m, 7d, 30d
    """
    if not duration_str:
        return None
    
    duration_str = duration_str.lower().strip()
    multiplier = 1
    
    if duration_str.endswith('d'):
        multiplier = 86400
        duration_str = duration_str[:-1]
    elif duration_str.endswith('h'):
        multiplier = 3600
        duration_str = duration_str[:-1]
    elif duration_str.endswith('m'):
        multiplier = 60
        duration_str = duration_str[:-1]
    
    try:
        value = int(duration_str)
        return value * multiplier
    except ValueError:
        return None


def safe_int(value, default: int = 0) -> int:
    """تبدیل امن به عدد صحیح"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """تبدیق امن به عدد اعشاری"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100) -> str:
    """بریدن متن اگر خیلی طولانی باشد"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """Escape کردن کاراکترهای Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def create_action_summary(actions: list) -> str:
    """ساخت خلاصه عملیات"""
    if not actions:
        return "هیچ تغییری اعمال نشد."
    
    summary = "خلاصه عملیات:\n"
    for action in actions:
        summary += f"• {action}\n"
    
    return summary


async def send_to_admins(
    context,
    message: str,
    exclude_user_id: int = None
):
    """ارسال پیام به تمام ادمین‌ها"""
    for admin_id in ADMIN_IDS:
        if exclude_user_id and admin_id == exclude_user_id:
            continue
        try:
            await context.bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send message to admin {admin_id}: {e}")


def get_command_args(context) -> list:
    """دریافت آرگومان‌های دستور"""
    if context.args:
        return context.args
    return []


def validate_user_id(user_id_str: str) -> Optional[int]:
    """اعتبارسنجی آیدی کاربر"""
    try:
        return int(user_id_str)
    except ValueError:
        return None


def format_user_info(user) -> str:
    """فرمت کردن اطلاعات کاربر"""
    info = []
    info.append(f"👤 <b>{user.first_name}</b>")
    if user.username:
        info.append(f"📛 @{user.username}")
    info.append(f"🆔 {user.user_id}")
    info.append(f"💰 {format_coins(user.coins)}")
    info.append(f"💎 {format_diamonds(user.diamonds)}")
    info.append(f"⚡ انرژی: {user.energy}/{user.max_energy}")
    info.append(f"📊 سطح: {user.click_level}")
    return "\n".join(info)


def get_timestamp() -> str:
    """دریافت زمان فعلی"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PermissionChecker:
    """کلاس بررسی سطح دسترسی"""
    
    @staticmethod
    def can_manage_users(user_id: int) -> bool:
        return is_admin(user_id)
    
    @staticmethod
    def can_manage_items(user_id: int) -> bool:
        return is_admin(user_id)
    
    @staticmethod
    def can_ban_users(user_id: int) -> bool:
        return get_admin_level(user_id) >= 2
    
    @staticmethod
    def can_broadcast(user_id: int) -> bool:
        return is_admin(user_id)
    
    @staticmethod
    def can_manage_settings(user_id: int) -> bool:
        return is_super_admin(user_id)
    
    @staticmethod
    def can_view_logs(user_id: int) -> bool:
        return is_super_admin(user_id)
    
    @staticmethod
    def can_manage_groups(user_id: int) -> bool:
        return is_admin(user_id)
