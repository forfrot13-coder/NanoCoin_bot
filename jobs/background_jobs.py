from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.connection import get_session
from database.models import User, UserQuest, QuestType
from datetime import datetime, timedelta

async def reset_daily_quests():
    session = get_session()
    # Delete old quests
    session.query(UserQuest).delete()
    
    # Create new quests for all users
    users = session.query(User).all()
    for user in users:
        q1 = UserQuest(
            user_id=user.user_id,
            code="daily_click",
            title="۱۰۰ کلیک امروز",
            quest_type=QuestType.CLICK,
            goal=100,
            reward_coins=500,
            reward_diamonds=1
        )
        session.add(q1)
    
    session.commit()
    session.close()

def setup_jobs(scheduler: AsyncIOScheduler):
    scheduler.add_job(reset_daily_quests, 'cron', hour=0, minute=0)
