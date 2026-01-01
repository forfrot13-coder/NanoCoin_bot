from sqlalchemy.orm import Session
from database.models import UserQuest, QuestType


class QuestService:
    """Service for quest management."""
    
    @staticmethod
    def update_quest_progress(session: Session, user_id: int, quest_type: str, amount: int):
        """Update progress for user's active quests of given type."""
        try:
            quest_type_enum = QuestType[quest_type]
        except KeyError:
            return
        
        quests = session.query(UserQuest).filter(
            UserQuest.user_id == user_id,
            UserQuest.quest_type == quest_type_enum,
            UserQuest.completed == False
        ).all()
        
        for quest in quests:
            quest.progress += amount
            if quest.progress >= quest.goal:
                quest.completed = True
                # Award rewards
                from database.models import User
                user = session.query(User).filter(User.user_id == user_id).first()
                if user:
                    user.coins += quest.reward_coins
                    user.diamonds += quest.reward_diamonds
                    user.click_xp += quest.reward_xp
    
    @staticmethod
    def get_user_quests(session: Session, user_id: int):
        """Get all quests for a user."""
        return session.query(UserQuest).filter(
            UserQuest.user_id == user_id
        ).all()
    
    @staticmethod
    def claim_quest_reward(session: Session, user_id: int, quest_id: int) -> tuple:
        """Claim reward for completed quest."""
        quest = session.query(UserQuest).filter(
            UserQuest.id == quest_id,
            UserQuest.user_id == user_id
        ).first()
        
        if not quest:
            return None, "Quest not found"
        
        if not quest.completed:
            return None, "Quest not completed yet"
        
        from database.models import User
        user = session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return None, "User not found"
        
        # Rewards already given when quest was completed
        # Just return the quest info
        return {
            "coins": quest.reward_coins,
            "diamonds": quest.reward_diamonds,
            "xp": quest.reward_xp
        }, None
