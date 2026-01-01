from datetime import datetime, timedelta
import random
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from database.models import User, GameItem, ItemType, Inventory
from backend.config import (
    BASE_CLICK_COINS, XP_PER_CLICK, XP_PER_LEVEL_BASE, XP_MULTIPLIER,
    MAX_ENERGY, MAX_ELECTRICITY, DIAMOND_DROP_CHANCE,
    ENERGY_REFILL_COST_DIAMONDS, ENERGY_REFILL_AMOUNT,
    BOOST_COST_DIAMONDS, BOOST_DURATION_MINUTES, BOOST_MULTIPLIER
)


class GameService:
    """Service for game logic operations."""
    
    @staticmethod
    def calculate_click_reward(user: User, session: Session) -> int:
        """Calculate coins reward for a single click."""
        # Base reward based on level
        reward = BASE_CLICK_COINS + (user.click_level - 1)
        
        # Check boost
        if user.active_boost_until and user.active_boost_until > datetime.now():
            reward *= user.boost_multiplier
        
        # Check artifacts (slot bonuses)
        slots = [user.slot_1_id, user.slot_2_id, user.slot_3_id]
        for slot_id in slots:
            if slot_id:
                item = session.query(GameItem).filter(GameItem.id == slot_id).first()
                if item:
                    reward += item.buff_click_coins
        
        return int(reward)
    
    @staticmethod
    def process_click(user: User, session: Session) -> Tuple[Optional[dict], Optional[str]]:
        """
        Process a click action.
        
        Returns:
            Tuple of (result_dict, error_message)
        """
        if user.energy <= 0:
            return None, "انرژی شما تمام شده است! ⚡️"
        
        reward = GameService.calculate_click_reward(user, session)
        user.coins += reward
        user.energy -= 1
        user.click_xp += XP_PER_CLICK
        
        # Check level up
        xp_needed = int(XP_PER_LEVEL_BASE * (user.click_level ** XP_MULTIPLIER))
        leveled_up = False
        if user.click_xp >= xp_needed:
            user.click_level += 1
            user.click_xp = 0
            leveled_up = True
        
        # Diamond drop
        diamond_found = False
        if random.random() < DIAMOND_DROP_CHANCE:
            diamond_found = True
            user.diamonds += 1
        
        # Update quest progress
        from backend.services.quest_service import QuestService
        QuestService.update_quest_progress(session, user.user_id, "CLICK", 1)
        
        return {
            "coins_earned": reward,
            "leveled_up": leveled_up,
            "diamond_found": diamond_found,
            "new_energy": user.energy,
            "new_coins": user.coins,
            "new_diamonds": user.diamonds,
            "new_level": user.click_level if leveled_up else None
        }, None
    
    @staticmethod
    def calculate_mining_rewards(
        user: User,
        inventory: list,
        session: Session,
        current_time: datetime
    ) -> Tuple[int, int, int, Optional[str]]:
        """
        Calculate mining rewards based on time passed and active miners.
        
        Returns:
            Tuple of (coins, electricity_spent, diamonds, error_message)
        """
        time_diff = current_time - user.last_mined_at
        hours_passed = time_diff.total_seconds() / 3600
        
        if hours_passed < (1/60):  # 1 minute minimum
            return 0, 0, 0, "لطفاً چند دقیقه صبر کنید"
        
        total_rate = 0
        total_consumption = 0
        diamond_chance = 0
        
        for inv_item in inventory:
            if inv_item.item.item_type == ItemType.MINER and inv_item.is_active:
                total_rate += inv_item.item.mining_rate * inv_item.quantity
                total_consumption += inv_item.item.electricity_consumption * inv_item.quantity
                diamond_chance = max(diamond_chance, inv_item.item.miner_diamond_chance)
        
        if total_rate == 0:
            return 0, 0, 0, "شما هیچ ماینر فعالی ندارید"
        
        # Apply artifacts bonuses for mining speed and luck
        slots = [user.slot_1_id, user.slot_2_id, user.slot_3_id]
        for slot_id in slots:
            if slot_id:
                item = session.query(GameItem).filter(GameItem.id == slot_id).first()
                if item:
                    if item.buff_mining_speed > 0:
                        total_rate *= (1 + item.buff_mining_speed)
                    if item.buff_luck > 0:
                        diamond_chance += item.buff_luck
        
        # Electricity check
        max_hours_by_electricity = user.electricity / total_consumption if total_consumption > 0 else hours_passed
        actual_hours = min(hours_passed, max_hours_by_electricity)
        
        if actual_hours <= 0:
            return 0, 0, 0, "برق کافی ندارید"
        
        coins_earned = int(total_rate * actual_hours)
        electricity_spent = int(total_consumption * actual_hours)
        
        diamonds_earned = 0
        if diamond_chance > 0 and actual_hours > 0:
            if random.random() < (diamond_chance * actual_hours):
                diamonds_earned = 1
        
        return coins_earned, electricity_spent, diamonds_earned, None
    
    @staticmethod
    def claim_mining_rewards(user: User, session: Session) -> Tuple[Optional[dict], Optional[str]]:
        """
        Claim mining rewards for a user.
        
        Returns:
            Tuple of (result_dict, error_message)
        """
        inventory = session.query(Inventory).filter(
            Inventory.user_id == user.user_id
        ).all()
        
        coins, electricity, diamonds, error = GameService.calculate_mining_rewards(
            user, inventory, session, datetime.now()
        )
        
        if error:
            return None, error
        
        user.coins += coins
        user.electricity -= electricity
        user.diamonds += diamonds
        user.last_mined_at = datetime.now()
        
        # Update quest progress
        from backend.services.quest_service import QuestService
        QuestService.update_quest_progress(session, user.user_id, "MINE", coins)
        
        return {
            "coins_earned": coins,
            "electricity_spent": electricity,
            "diamonds_earned": diamonds,
            "new_electricity": user.electricity,
            "new_coins": user.coins,
            "new_diamonds": user.diamonds
        }, None
    
    @staticmethod
    def refill_energy(user: User, amount: int = ENERGY_REFILL_AMOUNT) -> Tuple[bool, Optional[str]]:
        """
        Refill user energy using diamonds.
        
        Returns:
            Tuple of (success, error_message)
        """
        if user.diamonds < ENERGY_REFILL_COST_DIAMONDS:
            return False, "الماس کافی ندارید! 💎"
        
        user.diamonds -= ENERGY_REFILL_COST_DIAMONDS
        user.energy = min(user.energy + amount, user.max_energy)
        
        return True, None
    
    @staticmethod
    def activate_boost(user: User, duration_minutes: int = BOOST_DURATION_MINUTES) -> Tuple[bool, Optional[str]]:
        """
        Activate click boost for user.
        
        Returns:
            Tuple of (success, error_message)
        """
        if user.diamonds < BOOST_COST_DIAMONDS:
            return False, "الماس کافی ندارید! 💎"
        
        user.diamonds -= BOOST_COST_DIAMONDS
        user.boost_multiplier = BOOST_MULTIPLIER
        user.active_boost_until = datetime.now() + timedelta(minutes=duration_minutes)
        
        return True, None
    
    @staticmethod
    def claim_daily_reward(user: User, session: Session) -> Tuple[Optional[dict], Optional[str]]:
        """
        Claim daily reward for user.
        
        Returns:
            Tuple of (reward_dict, error_message)
        """
        from backend.config import DAILY_REWARDS_COINS, DAILY_REWARDS_DIAMONDS
        
        now = datetime.now()
        
        # Check if already claimed today
        if user.last_daily_claim:
            time_since_last = now - user.last_daily_claim
            if time_since_last.total_seconds() < 86400:  # 24 hours
                hours_left = int((86400 - time_since_last.total_seconds()) / 3600)
                return None, f"شما امروز جایزه دریافت کرده‌اید. {hours_left} ساعت دیگر برگردید"
            
            # Check streak
            if time_since_last.total_seconds() < 172800:  # 48 hours
                user.daily_streak += 1
            else:
                user.daily_streak = 1
        else:
            user.daily_streak = 1
        
        # Calculate reward based on streak
        day_index = min(user.daily_streak - 1, len(DAILY_REWARDS_COINS) - 1)
        coins_reward = DAILY_REWARDS_COINS[day_index]
        diamonds_reward = DAILY_REWARDS_DIAMONDS[day_index]
        
        user.coins += coins_reward
        user.diamonds += diamonds_reward
        user.last_daily_claim = now
        
        return {
            "coins": coins_reward,
            "diamonds": diamonds_reward,
            "streak": user.daily_streak
        }, None
