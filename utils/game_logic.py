from datetime import datetime, timedelta
import random
from config import (
    BASE_CLICK_COINS, XP_PER_CLICK, XP_PER_LEVEL_BASE, XP_MULTIPLIER, 
    MAX_ENERGY, MAX_ELECTRICITY, DIAMOND_DROP_CHANCE
)
from database.models import User, GameItem, ItemType

def calculate_click_reward(user: User, session):
    # Base reward based on level
    reward = BASE_CLICK_COINS + (user.click_level - 1)
    
    # Check boost
    if user.active_boost_until and user.active_boost_until > datetime.now():
        reward *= user.boost_multiplier
    
    # Check artifacts (slot bonuses)
    # This is a bit simplified, ideally we'd query the items in the slots
    slots = [user.slot_1_id, user.slot_2_id, user.slot_3_id]
    for slot_id in slots:
        if slot_id:
            item = session.query(GameItem).filter(GameItem.id == slot_id).first()
            if item:
                reward += item.buff_click_coins
                
    return int(reward)

def process_click(user: User, session):
    if user.energy <= 0:
        return None, "Low energy"
    
    reward = calculate_click_reward(user, session)
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
    diamond_found = 0
    if random.random() < DIAMOND_DROP_CHANCE:
        diamond_found = 1
        user.diamonds += 1
        
    return {
        "coins_earned": reward,
        "leveled_up": leveled_up,
        "diamond_found": diamond_found
    }, None

def calculate_mining_rewards(user: User, inventory, current_time: datetime):
    time_diff = current_time - user.last_mined_at
    hours_passed = time_diff.total_seconds() / 3600
    
    if hours_passed < (1/60): # 1 minute minimum
        return 0, 0, 0, "Too early"
    
    total_rate = 0
    total_consumption = 0
    diamond_chance = 0
    
    for inv_item in inventory:
        if inv_item.item.item_type == ItemType.MINER and inv_item.is_active:
            total_rate += inv_item.item.mining_rate * inv_item.quantity
            total_consumption += inv_item.item.electricity_consumption * inv_item.quantity
            diamond_chance = max(diamond_chance, inv_item.item.miner_diamond_chance)

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
    
    coins_earned = int(total_rate * actual_hours)
    electricity_spent = int(total_consumption * actual_hours)
    
    diamonds_earned = 0
    if diamond_chance > 0 and actual_hours > 0:
        # Simple diamond chance over time
        if random.random() < (diamond_chance * actual_hours):
            diamonds_earned = 1
            
    return coins_earned, electricity_spent, diamonds_earned, None
