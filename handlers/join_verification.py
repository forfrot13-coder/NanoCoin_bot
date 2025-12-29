import logging
from datetime import datetime
from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from sqlalchemy import and_
from database.connection import get_session
from database.models import User
from database.admin_models import JoinRequirement
from config import ADMIN_IDS
from utils.admin_helpers import is_admin, log_admin_action, format_datetime, safe_int
from utils.admin_keyboards import verification_keyboard, admin_back_keyboard, admin_join_keyboard

logger = logging.getLogger(__name__)


class JoinVerificationSystem:
    """سیستم بررسی عضویت اجباری"""
    
    def __init__(self):
        self.pending_verifications = {}  # user_id -> list of required chat_ids
    
    async def check_user_join_status(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
        """بررسی وضعیت عضویت کاربر در گروه‌های الزامی
        
        Returns:
            dict: {
                'is_member': bool,
                'missing_groups': list,
                'message': str,
                'keyboard': InlineKeyboardMarkup
            }
        """
        session = get_session()
        try:
            # دریافت تمام گروه‌های فعال
            requirements = session.query(JoinRequirement).filter(
                JoinRequirement.is_active == True
            ).all()
            
            if not requirements:
                return {
                    'is_member': True,
                    'missing_groups': [],
                    'message': None,
                    'keyboard': None
                }
            
            missing_groups = []
            bot = context.bot
            
            for req in requirements:
                try:
                    # بررسی عضویت در گروه/کانال
                    chat_member = await bot.get_chat_member(
                        chat_id=req.chat_id,
                        user_id=user_id
                    )
                    
                    # اگر کاربر عضو نیست
                    if chat_member.status not in ['member', 'administrator', 'creator']:
                        missing_groups.append(req)
                        
                except Exception as e:
                    logger.error(f"Error checking membership for {req.chat_id}: {e}")
                    # در صورت خطا، فرض می‌کنیم کاربر عضو نیست
                    missing_groups.append(req)
            
            if missing_groups:
                # ساخت پیام و کیبورد
                message_parts = ["❌ "]
                
                if len(missing_groups) == 1:
                    message_parts.append(f"لطفاً در گروه/کانال زیر عضو شوید:")
                else:
                    message_parts.append(f"لطفاً در {len(missing_groups)} گروه/کانال زیر عضو شوید:")
                
                message_text = "\n".join(message_parts) + "\n\n"
                
                # اضافه کردن لیست گروه‌ها
                group_list = []
                for req in missing_groups:
                    group_list.append(f"• {req.chat_name}")
                message_text += "\n".join(group_list)
                
                # پیام سفارشی اگر وجود دارد
                if missing_groups[0].error_message:
                    message_text = f"\n\n{missing_groups[0].error_message}"
                
                # ساخت کیبورد با لینک‌های جوین
                keyboard_buttons = []
                for req in missing_groups:
                    if req.invite_link:
                        keyboard_buttons.append([
                            InlineKeyboardButton(f"🔗 جوین در {req.chat_name[:20]}", url=req.invite_link)
                        ])
                
                keyboard_buttons.append([InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"verify_join_check_{user_id}")])
                
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                
                return {
                    'is_member': False,
                    'missing_groups': [req.chat_id for req in missing_groups],
                    'message': message_text,
                    'keyboard': keyboard
                }
            else:
                return {
                    'is_member': True,
                    'missing_groups': [],
                    'message': None,
                    'keyboard': None
                }
                
        finally:
            session.close()
    
    async def verify_and_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """بررسی و خوشامدگویی کاربر
        
        Returns:
            bool: True if user is verified, False otherwise
        """
        user_id = update.effective_user.id
        
        result = await self.check_user_join_status(user_id, context)
        
        if result['is_member']:
            return True
        else:
            # نمایش پیام خطا
            if update.message:
                await update.message.reply_text(
                    result['message'],
                    reply_markup=result['keyboard'],
                    parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.edit_message_text(
                    result['message'],
                    reply_markup=result['keyboard'],
                    parse_mode="Markdown"
                )
            return False


# نمونه سیستم
join_verification_system = JoinVerificationSystem()


# ========== CALLBACK HANDLERS ==========

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کال‌بک بررسی مجدد عضویت"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # بررسی مجدد وضعیت
    result = await join_verification_system.check_user_join_status(user_id, context)
    
    if result['is_member']:
        # کاربر عضو شده است
        await query.edit_message_text(
            "✅ **خوش آمدید!**\n\nشما با موفقیت در گروه‌های مورد نظر عضو شدید.\nاز بازی لذت ببرید! 🎮",
            parse_mode="Markdown"
        )
        await log_admin_action(update, "join_verify_success", "user", str(user_id), "User verified join successfully")
    else:
        # هنوز عضو نشده
        if result['keyboard']:
            await query.edit_message_text(
                result['message'],
                reply_markup=result['keyboard'],
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ هنوز در گروه‌های مورد نظر عضو نشده‌اید.\nلطفاً جوین شوید و دکمه بررسی مجدد را بزنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"verify_join_check_{user_id}")]
                ])
            )


async def verify_join_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کال‌بک بررسی مجدد با آیدی کاربر"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # استخراج آیدی کاربر از کال‌بک دیتا
    data = query.data
    parts = data.split("_")
    
    if len(parts) >= 4:
        target_user_id = int(parts[3])
        if target_user_id != user_id:
            # کاربر دیگری را بررسی می‌کند
            await query.answer("شما فقط می‌توانید وضعیت خودتان را بررسی کنید.", show_alert=True)
            return
    
    # بررسی وضعیت
    result = await join_verification_system.check_user_join_status(user_id, context)
    
    if result['is_member']:
        await query.edit_message_text(
            "✅ **خوش آمدید!**\n\nشما با موفقیت در گروه‌های مورد نظر عضو شدید.\nاز بازی لذت ببرید! 🎮",
            parse_mode="Markdown"
        )
        await log_admin_action(update, "join_verify_success", "user", str(user_id), "User verified join successfully")
    else:
        # نمایش مجدد پیام خطا
        if result['keyboard']:
            await query.edit_message_text(
                result['message'],
                reply_markup=result['keyboard'],
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ هنوز در گروه‌های مورد نظر عضو نشده‌اید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"verify_join_check_{user_id}")]
                ])
            )


# ========== ADMIN COMMANDS FOR JOIN MANAGEMENT ==========

async def admin_join_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تست بررسی عضویت برای یک کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_test [آیدی کاربر]")
        return
    
    target_id = safe_int(args[0], 0)
    if target_id == 0:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return
    
    result = await join_verification_system.check_user_join_status(target_id, context)
    
    if result['is_member']:
        await update.message.reply_text(f"✅ کاربر {target_id} در تمام گروه‌های الزامی عضو است.")
    else:
        missing_count = len(result['missing_groups'])
        await update.message.reply_text(
            f"❌ کاربر {target_id} در {missing_count} گروه/کانال عضو نیست.\n\nگروه‌های مورد نظر: {', '.join(result['missing_groups'])}"
        )


async def admin_join_check_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی وضعیت تمام کاربران"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    await update.message.reply_text("🔄 در حال بررسی وضعیت تمام کاربران...")
    
    session = get_session()
    try:
        users = session.query(User).all()
        verified_count = 0
        unverified_count = 0
        
        for user in users:
            result = await join_verification_system.check_user_join_status(user.user_id, context)
            if result['is_member']:
                verified_count += 1
            else:
                unverified_count += 1
        
        await update.message.reply_text(f"""
📊 **نتایج بررسی:**

✅ تأیید شده: {verified_count}
❌ تأیید نشده: {unverified_count}
👥 کل کاربران: {len(users)}
""", parse_mode="Markdown")
        
        await log_admin_action(update, "join_check_all", "users", str(len(users)), f"Verified: {verified_count}, Unverified: {unverified_count}")
    finally:
        session.close()


async def admin_join_remove_all_inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف تمام کاربران تأیید نشده"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        users = session.query(User).all()
        unverified_users = []
        
        for user in users:
            result = await join_verification_system.check_user_join_status(user.user_id, context)
            if not result['is_member']:
                unverified_users.append(user)
        
        if not unverified_users:
            await update.message.reply_text("✅ تمام کاربران تأیید شده‌اند.")
            return
        
        text = f"""
⚠️ **هشدار**

{len(unverified_users)} کاربر در گروه‌های الزامی عضو نیستند.

آیا می‌خواهید این کاربران را حذف کنید؟
(این عملیات برگشت‌پذیر نیست)
"""
        # ذخیره لیست کاربران برای تأیید
        context.user_data['pending_remove_users'] = [u.user_id for u in unverified_users]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ بله، حذف کن", callback_data="admin_join_confirm_remove")],
                [InlineKeyboardButton("❌ خیر", callback_data="admin_join")]
            ]),
            parse_mode="Markdown"
        )
    finally:
        session.close()


async def admin_join_confirm_remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید حذف کاربران تأیید نشده"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        return
    
    pending_users = context.user_data.get('pending_remove_users', [])
    
    if not pending_users:
        await query.edit_message_text("❌ لیست کاربران یافت نشد.")
        return
    
    session = get_session()
    try:
        deleted_count = 0
        for uid in pending_users:
            user = session.query(User).filter(User.user_id == uid).first()
            if user:
                # حذف داده‌های مرتبط
                from database.models import Inventory, UserAchievement, UserQuest, MarketListing
                session.query(Inventory).filter(Inventory.user_id == uid).delete()
                session.query(UserAchievement).filter(UserAchievement.user_id == uid).delete()
                session.query(UserQuest).filter(UserQuest.user_id == uid).delete()
                session.query(MarketListing).filter(MarketListing.seller_id == uid).delete()
                session.query(User).filter(User.user_id == uid).delete()
                deleted_count += 1
        
        session.commit()
        
        await query.edit_message_text(f"✅ {deleted_count} کاربر حذف شد.")
        await log_admin_action(update, "join_remove_inactive", "users", str(deleted_count), f"Removed {deleted_count} unverified users")
    except Exception as e:
        await query.edit_message_text(f"❌ خطا: {str(e)}")
    finally:
        session.close()


async def admin_join_import_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن تمام اعضای یک گروه به لیست تأیید شده‌ها"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_import [چت آیدی گروه]")
        return
    
    chat_id = args[0]
    
    try:
        bot = context.bot
        members = []
        offset = None
        
        while True:
            # دریافت لیست اعضا
            chat_members = await bot.get_chat_administrators(chat_id=chat_id)
            members.extend([m.user.id for m in chat_members])
            break  # فعلاً فقط ادمین‌ها
        
        if members:
            text = f"""
📥 **اعضای یافت شده**

تعداد اعضای قابل بررسی: {len(members)}

⚠️ توجه: این دستور فقط ادمین‌های گروه را برمی‌گرداند.
برای دریافت تمام اعضا، ربات باید در گروه عضو باشد و دسترسی لازم را داشته باشد.
"""
        else:
            text = "❌ هیچ عضوی یافت نشد."
        
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")


async def admin_join_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار سیستم جوین"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        active_reqs = [r for r in requirements if r.is_active]
        
        text = f"""
📊 **آمار سیستم عضویت اجباری**

📌 **الزامات:**
• کل الزامات: {len(requirements)}
• فعال: {len(active_reqs)}
• غیرفعال: {len(requirements) - len(active_reqs)}

📋 **لیست گروه‌ها:**
"""
        
        for req in requirements:
            status = "✅" if req.is_active else "❌"
            text += f"{status} {req.chat_name} ({req.chat_id})\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


# ========== VERIFICATION IN START HANDLER ==========

async def check_verification_on_start(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """بررسی تأیید عضویت هنگام استارت
    
    Returns:
        tuple: (is_verified, message, keyboard)
    """
    result = await join_verification_system.check_user_join_status(user_id, context)
    
    if result['is_member']:
        return (True, None, None)
    else:
        return (False, result['message'], result['keyboard'])


# ========== REGISTER HANDLERS ==========

def register_join_verification_handlers(application):
    """ثبت هندلرهای سیستم جوین"""
    
    # کال‌بک‌های بررسی
    application.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(verify_join_check_callback, pattern="^verify_join_check_"))
    
    # کال‌بک تأیید حذف
    application.add_handler(CallbackQueryHandler(admin_join_confirm_remove_callback, pattern="^admin_join_confirm_remove$"))
    
    # دستورات ادمین
    application.add_handler(CommandHandler("admin_join_test", admin_join_test))
    application.add_handler(CommandHandler("admin_join_check_all", admin_join_check_all))
    application.add_handler(CommandHandler("admin_join_remove_all_inactive", admin_join_remove_all_inactive))
    application.add_handler(CommandHandler("admin_join_import", admin_join_import_from_group))
    application.add_handler(CommandHandler("admin_join_stats", admin_join_stats))


# ========== HELPER FUNCTIONS ==========

async def force_verify_user(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اجبار به تأیید عضویت
    
    Returns:
        bool: True if user is now verified
    """
    result = await join_verification_system.check_user_join_status(user_id, context)
    return result['is_member']


async def get_missing_groups(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> List[JoinRequirement]:
    """دریافت لیست گروه‌هایی که کاربر در آن‌ها عضو نیست"""
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).filter(
            JoinRequirement.is_active == True
        ).all()
        
        missing = []
        bot = context.bot
        
        for req in requirements:
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=req.chat_id,
                    user_id=user_id
                )
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    missing.append(req)
            except Exception:
                missing.append(req)
        
        return missing
    finally:
        session.close()


async def get_user_verification_status(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """دریافت وضعیت کامل تأیید کاربر"""
    result = await join_verification_system.check_user_join_status(user_id, context)
    
    session = get_session()
    try:
        requirements = session.query(JoinRequirement).filter(
            JoinRequirement.is_active == True
        ).all()
        
        groups_status = []
        bot = context.bot
        
        for req in requirements:
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=req.chat_id,
                    user_id=user_id
                )
                is_member = chat_member.status in ['member', 'administrator', 'creator']
            except Exception:
                is_member = False
            
            groups_status.append({
                'chat_id': req.chat_id,
                'chat_name': req.chat_name,
                'is_member': is_member
            })
        
        return {
            'is_verified': result['is_member'],
            'missing_count': len(result['missing_groups']),
            'groups': groups_status
        }
    finally:
        session.close()
