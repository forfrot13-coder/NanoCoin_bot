import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, DATABASE_URL
from database.connection import init_db
from handlers.start import start, main_menu_callback
from handlers.game import click_handler, mine_handler
from handlers.shop import shop_main, shop_buy
from handlers.market import market_main, market_buy
from handlers.casino import casino_main, casino_slots, casino_crash
from handlers.profile import profile_main, inventory_main, inventory_toggle, leaderboard_main
from handlers.quests import quests_main
from handlers.achievements import achievements_main
from handlers.admin import admin_add_item, admin_stats
from handlers.admin_panel import (
    admin_panel, admin_users, admin_items_cmd, admin_stats_cmd, admin_leaderboard,
    admin_search_user, admin_give_coins, admin_give_diamonds, admin_ban_user,
    admin_unban_user, admin_reset_user, admin_delete_user, admin_add_item_cmd,
    admin_set_price, admin_item_stats, admin_join_settings, admin_join_add,
    admin_join_remove, admin_join_list, admin_join_message, admin_join_toggle,
    admin_broadcast_cmd, admin_dm, admin_announce, admin_active_users,
    admin_panel_callback, register_admin_handlers
)
from handlers.join_verification import (
    verify_join_callback, verify_join_check_callback,
    admin_join_test, admin_join_check_all, admin_join_remove_all_inactive,
    admin_join_confirm_remove_callback, admin_join_import_from_group, admin_join_stats,
    register_join_verification_handlers
)
from jobs.background_jobs import setup_jobs
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Exception while handling an update: {context.error}")

def main():
    # Initialize Database
    init_db()

    # Scheduler
    scheduler = AsyncIOScheduler()
    setup_jobs(scheduler)
    scheduler.start()

    # Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Basic Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("additem", admin_add_item))
    application.add_handler(CommandHandler("stats", admin_stats))

    # Menu Callback Handlers
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(click_handler, pattern="^game_click$"))
    application.add_handler(CallbackQueryHandler(mine_handler, pattern="^game_mine$"))
    application.add_handler(CallbackQueryHandler(shop_main, pattern="^shop_main$"))
    application.add_handler(CallbackQueryHandler(shop_buy, pattern="^shop_buy_"))
    application.add_handler(CallbackQueryHandler(market_main, pattern="^market_main$"))
    application.add_handler(CallbackQueryHandler(market_buy, pattern="^market_buy_"))
    application.add_handler(CallbackQueryHandler(casino_main, pattern="^casino_main$"))
    application.add_handler(CallbackQueryHandler(casino_slots, pattern="^casino_slots$"))
    application.add_handler(CallbackQueryHandler(casino_crash, pattern="^casino_crash$"))
    application.add_handler(CallbackQueryHandler(profile_main, pattern="^profile_main$"))
    application.add_handler(CallbackQueryHandler(inventory_main, pattern="^inventory_main$"))
    application.add_handler(CallbackQueryHandler(inventory_toggle, pattern="^inv_toggle_"))
    application.add_handler(CallbackQueryHandler(leaderboard_main, pattern="^leaderboard_main$"))
    application.add_handler(CallbackQueryHandler(quests_main, pattern="^quests_main$"))
    application.add_handler(CallbackQueryHandler(achievements_main, pattern="^achievements_main$"))

    # Admin Panel Handlers
    register_admin_handlers(application)

    # Join Verification Handlers
    register_join_verification_handlers(application)

    # Error Handler
    application.add_error_handler(error_handler)

    # Run
    logging.info("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
