import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
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
    
    async def check_user_join_status(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, retry_on_error: bool = True) -> Dict[str, Any]:
        """بررسی وضعیت عضویت کاربر در گروه‌های الزامی با مدیریت خطا بهتر

        Args:
            user_id: آیدی کاربر
            context: ContextTypes.DEFAULT_TYPE
            retry_on_error: تلاش مجدد در صورت خطا

        Returns:
            dict: {
                'is_member': bool,
                'missing_groups': list,
                'message': str,
                'keyboard': InlineKeyboardMarkup,
                'details': dict - جزئیات وضعیت هر گروه
            }
        """
        session = get_session()
        try:
            # دریافت تمام گروه‌های فعال
            requirements = session.query(JoinRequirement).filter(
                JoinRequirement.is_active == True
            ).all()

            if not requirements:
                logger.info(f"User {user_id}: No join requirements configured")
                return {
                    'is_member': True,
                    'missing_groups': [],
                    'message': None,
                    'keyboard': None,
                    'details': {}
                }

            missing_groups = []
            group_details = {}
            bot = context.bot

            for req in requirements:
                group_info = {
                    'chat_id': req.chat_id,
                    'chat_name': req.chat_name,
                    'is_member': False,
                    'status': None,
                    'error': None
                }

                try:
                    # بررسی عضویت در گروه/کانال با timeout
                    chat_member = await asyncio.wait_for(
                        bot.get_chat_member(
                            chat_id=req.chat_id,
                            user_id=user_id
                        ),
                        timeout=10.0
                    )

                    # اگر کاربر عضو است (member, administrator, creator)
                    if chat_member.status in ['member', 'administrator', 'creator']:
                        group_info['is_member'] = True
                        group_info['status'] = chat_member.status
                        logger.debug(f"User {user_id} is member of {req.chat_name} ({chat_member.status})")
                    else:
                        group_info['status'] = chat_member.status
                        group_info['is_member'] = False
                        missing_groups.append(req)
                        logger.warning(f"User {user_id} status in {req.chat_name}: {chat_member.status}")

                    group_details[req.chat_id] = group_info

                except asyncio.TimeoutError:
                    logger.error(f"Timeout checking membership for {req.chat_id}")
                    group_info['error'] = 'timeout'
                    group_details[req.chat_id] = group_info

                    if retry_on_error:
                        # تلاش مجدد یک بار
                        try:
                            await asyncio.sleep(1)
                            chat_member = await bot.get_chat_member(
                                chat_id=req.chat_id,
                                user_id=user_id
                            )
                            if chat_member.status in ['member', 'administrator', 'creator']:
                                group_info['is_member'] = True
                                group_info['status'] = chat_member.status
                            else:
                                missing_groups.append(req)
                        except Exception as retry_error:
                            logger.error(f"Retry failed for {req.chat_id}: {retry_error}")
                            missing_groups.append(req)
                    else:
                        missing_groups.append(req)

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error checking membership for {req.chat_id}: {error_msg}")
                    group_info['error'] = error_msg
                    group_details[req.chat_id] = group_info

                    # بررسی نوع خطا - برخی خطاها به معنی عدم عضویت نیستند
                    if "not found" in error_msg.lower() or "user" in error_msg.lower():
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
                    message_text += f"\n\n{missing_groups[0].error_message}"

                # ساخت کیبورد با لینک‌های جوین
                keyboard_buttons = []
                for req in missing_groups:
                    if req.invite_link:
                        keyboard_buttons.append([
                            InlineKeyboardButton(f"🔗 جوین در {req.chat_name[:20]}", url=req.invite_link)
                        ])

                keyboard_buttons.append([InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"verify_join_check_{user_id}")])

                keyboard = InlineKeyboardMarkup(keyboard_buttons)

                logger.info(f"User {user_id}: Not verified - missing {len(missing_groups)} groups")

                return {
                    'is_member': False,
                    'missing_groups': [req.chat_id for req in missing_groups],
                    'message': message_text,
                    'keyboard': keyboard,
                    'details': group_details
                }
            else:
                logger.info(f"User {user_id}: Verified successfully")
                return {
                    'is_member': True,
                    'missing_groups': [],
                    'message': None,
                    'keyboard': None,
                    'details': group_details
                }

        finally:
            session.close()
    
    async def verify_and_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE, show_details: bool = False) -> bool:
        """بررسی و خوشامدگویی کاربر با پیام تفصیلی‌تر

        Args:
            update: Update object
            context: ContextTypes.DEFAULT_TYPE
            show_details: نمایش جزئیات بیشتر

        Returns:
            bool: True if user is verified, False otherwise
        """
        user_id = update.effective_user.id

        result = await self.check_user_join_status(user_id, context)

        if result['is_member']:
            return True
        else:
            # نمایش پیام خطا با جزئیات بیشتر
            message = result['message']
            keyboard = result['keyboard']

            if show_details and result.get('details'):
                # اضافه کردن جزئیات هر گروه
                details_text = "\n\n📋 **جزئیات وضعیت:**\n"
                for chat_id, info in result['details'].items():
                    status_emoji = "✅" if info['is_member'] else "❌"
                    status_text = info['status'] or 'نامشخص'
                    error_text = f"\n   ⚠️ {info['error']}" if info.get('error') else ""
                    details_text += f"{status_emoji} {info['chat_name']}: {status_text}{error_text}\n"

                message += details_text

            # نمایش پیام
            if update.message:
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=keyboard,
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


async def admin_join_verify_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تست تفصیلی وضعیت عضویت یک کاربر"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ فرمت صحیح: /admin_join_verify_test [آیدی کاربر]")
        return

    target_id = safe_int(args[0], 0)
    if target_id == 0:
        await update.message.reply_text("❌ آیدی نامعتبر است.")
        return

    await update.message.reply_text(f"🔍 در حال بررسی کاربر {target_id}...")

    # بررسی تفصیلی وضعیت
    result = await join_verification_system.check_user_join_status(target_id, context)

    # دریافت اطلاعات کاربر
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == target_id).first()
        user_info = ""
        if user:
            user_info = f"""
👤 **اطلاعات کاربر:**
• نام: {user.first_name or 'نامشخص'}
• یوزرنیم: @{user.username if user.username else 'ندارد'}
• آیدی: {user.user_id}
• سکه: {user.coins}
• الماس: {user.diamonds}
"""
        else:
            user_info = f"⚠️ کاربر {target_id} در دیتابیس یافت نشد.\n"
    finally:
        session.close()

    # ساخت گزارش تفصیلی
    report = f"""
📋 **گزارش بررسی عضویت کاربر**

{user_info}

{'✅' if result['is_member'] else '❌'} **وضعیت کلی:** {'تأیید شده' if result['is_member'] else 'تأیید نشده'}

📊 **وضعیت گروه‌ها:**
"""

    details = result.get('details', {})
    if details:
        for chat_id, info in details.items():
            status_emoji = "✅" if info['is_member'] else "❌"
            status_text = info['status'] or 'نامشخص'
            error_text = f"\n   ⚠️ خطا: {info['error']}" if info.get('error') else ""

            report += f"""
{status_emoji} {info['chat_name']} ({chat_id})
   وضعیت: {status_text}{error_text}
"""
    else:
        report += "• هیچ گروهی تنظیم نشده است.\n"

    if not result['is_member']:
        report += f"\n📌 گروه‌های مورد نیاز: {len(result['missing_groups'])}"
        report += "\n" + ", ".join(result['missing_groups'])

    # دکمه‌های کاربردی
    keyboard_buttons = []
    if not result['is_member']:
        keyboard_buttons.append([
            InlineKeyboardButton("📊 بررسی همه کاربران", callback_data="admin_join_verify_all")
        ])
    keyboard_buttons.append([InlineKeyboardButton("🔍 دیباگ سیستم", callback_data="admin_join_debug")])
    keyboard_buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")])

    keyboard = InlineKeyboardMarkup(keyboard_buttons) if keyboard_buttons else None

    await update.message.reply_text(report, reply_markup=keyboard, parse_mode="Markdown")
    await log_admin_action(update, "join_verify_test", "user", str(target_id), f"Verified: {result['is_member']}")


async def admin_join_verify_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تست تفصیلی تمام کاربران"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    await update.message.reply_text("🔄 در حال بررسی وضعیت تمام کاربران... این ممکن است چند لحظه طول بکشد.")

    session = get_session()
    try:
        users = session.query(User).all()
        verified_count = 0
        unverified_count = 0
        unverified_users = []

        total = len(users)
        processed = 0

        for user in users:
            result = await join_verification_system.check_user_join_status(user.user_id, context)
            processed += 1

            if result['is_member']:
                verified_count += 1
            else:
                unverified_count += 1
                unverified_users.append(user)

            # نمایش پیشرفت هر 10 کاربر
            if processed % 10 == 0:
                logger.info(f"Processed {processed}/{total} users")

        # ساخت گزارش آماری
        percentage = (verified_count / total * 100) if total > 0 else 0

        report = f"""
📊 **گزارش کامل بررسی کاربران**

📈 **آمار کلی:**
✅ تأیید شده: {verified_count} ({percentage:.1f}%)
❌ تأیید نشده: {unverified_count} ({100 - percentage:.1f}%)
👥 کل کاربران: {total}

📋 **کاربران تأیید نشده:**
"""

        if unverified_users:
            for user in unverified_users[:20]:  # فقط 20 نفر اول
                user_name = user.first_name or 'نامشخص'
                username = f"(@{user.username})" if user.username else ""
                report += f"• {user_name} {username} - {user.user_id}\n"

            if len(unverified_users) > 20:
                report += f"\n... و {len(unverified_users) - 20} کاربر دیگر"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 حذف کاربران تأیید نشده", callback_data="admin_join_remove_all_inactive")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
            ])
        else:
            report += "• همه کاربران تأیید شده‌اند! 🎉"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
            ])

        await update.message.reply_text(report, reply_markup=keyboard, parse_mode="Markdown")
        await log_admin_action(
            update,
            "join_verify_all",
            "users",
            str(total),
            f"Verified: {verified_count}, Unverified: {unverified_count}"
        )

    finally:
        session.close()


async def admin_join_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دیباگ سیستم جوین اجباری"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    await update.message.reply_text("🔍 در حال جمع‌آوری اطلاعات سیستم...")

    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        bot = context.bot

        report = """
🔍 **دیباگ سیستم جوین اجباری**

📋 **گروه‌های تنظیم شده:**
"""

        if not requirements:
            report += "• هیچ گروهی تنظیم نشده است.\n"
        else:
            for req in requirements:
                status_emoji = "✅" if req.is_active else "❌"
                report += f"""
{status_emoji} **{req.chat_name}**
   📌 آیدی: {req.chat_id}
   📝 نوع: {req.chat_type or 'نامشخص'}
   🔗 لینک دعوت: {req.invite_link or 'تنظیم نشده'}
   📨 پیام: {'تنظیم شده' if req.message else 'پیش‌فرض'}
   ⚙️ وضعیت: {'فعال' if req.is_active else 'غیرفعال'}
"""

                # بررسی دسترسی ربات به گروه
                try:
                    chat = await bot.get_chat(req.chat_id)
                    report += f"   🤖 دسترسی ربات: ✅ (نام: {chat.title})\n"

                    # بررسی ادمین بودن ربات
                    try:
                        bot_member = await bot.get_chat_member(chat_id=req.chat_id, user_id=bot.id)
                        is_admin = bot_member.status in ['administrator', 'creator']
                        report += f"   👔 وضعیت ادمین: {'✅' if is_admin else '❌'} ({bot_member.status})\n"
                    except Exception as e:
                        report += f"   👔 وضعیت ادمین: ❌ خطا: {str(e)[:50]}\n"

                except Exception as e:
                    report += f"   🤖 دسترسی ربات: ❌ {str(e)[:50]}\n"

                report += "\n"

        # تست ربات
        report += """
📊 **تست سیستم:**
"""
        bot_info = await bot.get_me()
        report += f"""
• نام ربات: @{bot_info.username}
• آیدی ربات: {bot_info.id}
• وضعیت: ✅ آنلاین
"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بررسی همه کاربران", callback_data="admin_join_verify_all")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
        ])

        await update.message.reply_text(report, reply_markup=keyboard, parse_mode="Markdown")
        await log_admin_action(update, "join_debug", "system", "debug", "System debug completed")

    finally:
        session.close()


async def admin_join_verify_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کال‌بک بررسی همه کاربران"""
    query = update.callback_query
    await query.answer("در حال بررسی...")

    user_id = query.from_user.id
    if not is_admin(user_id):
        return

    # دریافت اطلاعات برای تابع اصلی
    # چون تابع اصلی از update.message استفاده می‌کند، باید یک آبجکت mock بسازیم
    # اما بهتر است پیام را جداگانه ارسال کنیم
    await query.edit_message_text("🔄 در حال بررسی وضعیت تمام کاربران... این ممکن است چند لحظه طول بکشد.")

    session = get_session()
    try:
        users = session.query(User).all()
        verified_count = 0
        unverified_count = 0
        unverified_users = []

        total = len(users)
        processed = 0

        for user in users:
            result = await join_verification_system.check_user_join_status(user.user_id, context)
            processed += 1

            if result['is_member']:
                verified_count += 1
            else:
                unverified_count += 1
                unverified_users.append(user)

            if processed % 10 == 0:
                logger.info(f"Processed {processed}/{total} users")

        percentage = (verified_count / total * 100) if total > 0 else 0

        report = f"""
📊 **گزارش کامل بررسی کاربران**

📈 **آمار کلی:**
✅ تأیید شده: {verified_count} ({percentage:.1f}%)
❌ تأیید نشده: {unverified_count} ({100 - percentage:.1f}%)
👥 کل کاربران: {total}

📋 **کاربران تأیید نشده:**
"""

        if unverified_users:
            for user in unverified_users[:20]:
                user_name = user.first_name or 'نامشخص'
                username = f"(@{user.username})" if user.username else ""
                report += f"• {user_name} {username} - {user.user_id}\n"

            if len(unverified_users) > 20:
                report += f"\n... و {len(unverified_users) - 20} کاربر دیگر"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 حذف کاربران تأیید نشده", callback_data="admin_join_confirm_remove")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
            ])
        else:
            report += "• همه کاربران تأیید شده‌اند! 🎉"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
            ])

        await query.edit_message_text(report, reply_markup=keyboard, parse_mode="Markdown")
        await log_admin_action(
            update,
            "join_verify_all",
            "users",
            str(total),
            f"Verified: {verified_count}, Unverified: {unverified_count}"
        )

    finally:
        session.close()


async def admin_join_debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کال‌بک دیباگ سیستم"""
    query = update.callback_query
    await query.answer("در حال دیباگ...")

    user_id = query.from_user.id
    if not is_admin(user_id):
        return

    session = get_session()
    try:
        requirements = session.query(JoinRequirement).all()
        bot = context.bot

        report = """
🔍 **دیباگ سیستم جوین اجباری**

📋 **گروه‌های تنظیم شده:**
"""

        if not requirements:
            report += "• هیچ گروهی تنظیم نشده است.\n"
        else:
            for req in requirements:
                status_emoji = "✅" if req.is_active else "❌"
                report += f"""
{status_emoji} **{req.chat_name}**
   📌 آیدی: {req.chat_id}
   📝 نوع: {req.chat_type or 'نامشخص'}
   🔗 لینک دعوت: {req.invite_link or 'تنظیم نشده'}
   📨 پیام: {'تنظیم شده' if req.message else 'پیش‌فرض'}
   ⚙️ وضعیت: {'فعال' if req.is_active else 'غیرفعال'}
"""

                try:
                    chat = await bot.get_chat(req.chat_id)
                    report += f"   🤖 دسترسی ربات: ✅ (نام: {chat.title})\n"

                    try:
                        bot_member = await bot.get_chat_member(chat_id=req.chat_id, user_id=bot.id)
                        is_admin = bot_member.status in ['administrator', 'creator']
                        report += f"   👔 وضعیت ادمین: {'✅' if is_admin else '❌'} ({bot_member.status})\n"
                    except Exception as e:
                        report += f"   👔 وضعیت ادمین: ❌ خطا: {str(e)[:50]}\n"

                except Exception as e:
                    report += f"   🤖 دسترسی ربات: ❌ {str(e)[:50]}\n"

                report += "\n"

        report += """
📊 **تست سیستم:**
"""
        bot_info = await bot.get_me()
        report += f"""
• نام ربات: @{bot_info.username}
• آیدی ربات: {bot_info.id}
• وضعیت: ✅ آنلاین
"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بررسی همه کاربران", callback_data="admin_join_verify_all")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_join")]
        ])

        await query.edit_message_text(report, reply_markup=keyboard, parse_mode="Markdown")
        await log_admin_action(update, "join_debug", "system", "debug", "System debug completed")

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

    # کال‌بک‌های جدید
    application.add_handler(CallbackQueryHandler(admin_join_verify_all_callback, pattern="^admin_join_verify_all$"))
    application.add_handler(CallbackQueryHandler(admin_join_debug_callback, pattern="^admin_join_debug$"))

    # دستورات ادمین
    application.add_handler(CommandHandler("admin_join_test", admin_join_test))
    application.add_handler(CommandHandler("admin_join_check_all", admin_join_check_all))
    application.add_handler(CommandHandler("admin_join_remove_all_inactive", admin_join_remove_all_inactive))
    application.add_handler(CommandHandler("admin_join_import", admin_join_import_from_group))
    application.add_handler(CommandHandler("admin_join_stats", admin_join_stats))

    # دستورات جدید تست و دیباگ
    application.add_handler(CommandHandler("admin_join_verify_test", admin_join_verify_test))
    application.add_handler(CommandHandler("admin_join_verify_all", admin_join_verify_all))
    application.add_handler(CommandHandler("admin_join_debug", admin_join_debug))


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
