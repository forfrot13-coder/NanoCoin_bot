from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import datetime


class Base(DeclarativeBase):
    pass


class JoinRequirement(Base):
    """مدل الزام عضویت در گروه/کانال"""
    __tablename__ = 'join_requirements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), unique=True, nullable=False)  # گروپ/چنل
    chat_name = Column(String(255))  # نام گروپ/چنل
    chat_type = Column(String(20))  # GROUP, SUPERGROUP, CHANNEL
    invite_link = Column(String(500), nullable=True)  # لینک دعوت
    message = Column(Text)  # پیام دعوت
    error_message = Column(Text, default="لطفاً ابتدا در گروه/کانال ما جوین کنید و سپس دکمه بررسی را بزنید.")  # پیام خطا
    is_active = Column(Boolean, default=True)
    required_for_all = Column(Boolean, default=True)  # الزامی برای همه
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(BigInteger)  # ادمین سازنده

    def __repr__(self):
        return f"<JoinRequirement(id={self.id}, chat_id={self.chat_id}, chat_name={self.chat_name})>"


class AdminLog(Base):
    """مدل لاگ عملیات ادمین"""
    __tablename__ = 'admin_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    admin_username = Column(String, nullable=True)
    action = Column(String(100), nullable=False)  # add_item, ban_user, etc.
    target_type = Column(String(50), nullable=True)  # user, item, group, etc.
    target_id = Column(String(100), nullable=True)
    details = Column(Text)  # جزئیات عملیات
    ip_address = Column(String(45), nullable=True)  # آدرس IP
    user_agent = Column(String(500), nullable=True)  # User Agent
    timestamp = Column(DateTime, default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AdminLog(id={self.id}, admin_id={self.admin_id}, action={self.action})>"


class AdminSettings(Base):
    """مدل تنظیمات ادمین"""
    __tablename__ = 'admin_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(20), default='string')  # string, int, bool, json
    description = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AdminSettings(key={self.setting_key}, value={self.setting_value})>"


class BroadcastMessage(Base):
    """مدل پیام‌های همگانی"""
    __tablename__ = 'broadcast_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_text = Column(Text, nullable=False)
    message_type = Column(String(20), default='text')  # text, photo, audio, etc.
    media_file_id = Column(String(500), nullable=True)
    keyboard = Column(Text, nullable=True)  # JSON keyboard data
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=func.now())
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')  # pending, sending, completed, failed

    def __repr__(self):
        return f"<BroadcastMessage(id={self.id}, status={self.status})>"


class UserWarning(Base):
    """مدل هشدار کاربران"""
    __tablename__ = 'user_warnings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    warning_type = Column(String(50), nullable=False)  # spam, abuse, cheating, etc.
    reason = Column(Text)
    issued_by = Column(BigInteger)
    issued_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<UserWarning(id={self.id}, user_id={self.user_id}, type={self.warning_type})>"


class BannedUser(Base):
    """مدل کاربران مسدود شده"""
    __tablename__ = 'banned_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    reason = Column(Text)
    banned_by = Column(BigInteger)
    banned_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)  # None = permanent
    is_permanent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<BannedUser(user_id={self.user_id}, permanent={self.is_permanent})>"


class GroupManagement(Base):
    """مدل مدیریت گروه‌ها"""
    __tablename__ = 'group_management'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), unique=True, nullable=False)
    chat_name = Column(String(255))
    chat_type = Column(String(20))
    is_premium = Column(Boolean, default=False)  # گروه پولی
    is_active = Column(Boolean, default=True)
    settings = Column(Text)  # JSON تنظیمات
    added_by = Column(BigInteger)
    added_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<GroupManagement(chat_id={self.chat_id}, chat_name={self.chat_name})>"


class ScheduledTask(Base):
    """مدل وظایف زمان‌بندی شده"""
    __tablename__ = 'scheduled_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)  # broadcast, cleanup, etc.
    task_data = Column(Text)  # JSON data
    scheduled_at = Column(DateTime, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=func.now())
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, type={self.task_type}, status={self.status})>"


class SystemStats(Base):
    """مدل آمار سیستم"""
    __tablename__ = 'system_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_type = Column(String(50), nullable=False)  # users, economy, items, etc.
    stat_value = Column(Text)  # JSON value
    stat_date = Column(DateTime, default=func.now())
    recorded_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<SystemStats(type={self.stat_type}, date={self.stat_date})>"


class AdminNotification(Base):
    """مدل اعلان‌های ادمین"""
    __tablename__ = 'admin_notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type = Column(String(50), nullable=False)  # warning, alert, info
    title = Column(String(255))
    message = Column(Text)
    priority = Column(Integer, default=0)  # 0=low, 1=normal, 2=high, 3=critical
    is_read = Column(Boolean, default=False)
    read_by = Column(BigInteger, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AdminNotification(id={self.id}, type={self.notification_type})>"


class AntiSpamConfig(Base):
    """مدل تنظیمات ضد اسپم"""
    __tablename__ = 'anti_spam_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(20), default='string')
    description = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AntiSpamConfig(key={self.config_key}, value={self.config_value})>"


class DailyStats(Base):
    """مدل آمار روزانه"""
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, default=func.now().date())
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    total_messages = Column(BigInteger, default=0)
    total_clicks = Column(BigInteger, default=0)
    total_mining = Column(BigInteger, default=0)
    new_items_sold = Column(Integer, default=0)
    market_transactions = Column(Integer, default=0)
    economy_volume = Column(BigInteger, default=0)  # total coins traded
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<DailyStats(date={self.stat_date}, new_users={self.new_users})>"


class PremiumUser(Base):
    """مدل کاربران پرمیوم"""
    __tablename__ = 'premium_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    premium_type = Column(String(20), default='vip')  # vip, premium, gold
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime, nullable=True)
    granted_by = Column(BigInteger)
    bonus_coins = Column(BigInteger, default=0)
    bonus_diamonds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PremiumUser(user_id={self.user_id}, type={self.premium_type})>"


class GameEvent(Base):
    """مدل رویدادهای بازی"""
    __tablename__ = 'game_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # bonus, drop, tournament
    description = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    bonus_multiplier = Column(Float, default=1.0)
    special_rewards = Column(Text)  # JSON rewards
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<GameEvent(id={self.id}, name={self.event_name}, type={self.event_type})>"


class ReferralCode(Base):
    """مدل کدهای رفرال"""
    __tablename__ = 'referral_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    referrer_id = Column(BigInteger, nullable=False)
    referrer_username = Column(String, nullable=True)
    reward_coins = Column(BigInteger, default=0)
    reward_diamonds = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer, default=0)  # 0 = unlimited
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ReferralCode(code={self.code}, referrer={self.referrer_id})>"


class ReferralUse(Base):
    """مدل استفاده از کدهای رفرال"""
    __tablename__ = 'referral_uses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    referral_code_id = Column(Integer, ForeignKey('referral_codes.id'), nullable=False)
    referrer_id = Column(BigInteger, nullable=False)
    referred_id = Column(BigInteger, nullable=False)
    reward_claimed = Column(Boolean, default=False)
    used_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<ReferralUse(code={self.referral_code_id}, referred={self.referred_id})>"
