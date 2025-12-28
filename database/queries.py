from sqlalchemy.orm import Session
from database.models import User, GameItem, Inventory, MarketListing, Achievement, UserAchievement, UserQuest, PromoCode, UsedPromo, ItemType
from datetime import datetime, timedelta
from sqlalchemy import func

def get_user(session: Session, user_id: int):
    return session.query(User).filter(User.user_id == user_id).first()

def create_user(session: Session, user_id: int, username: str, first_name: str):
    user = User(user_id=user_id, username=username, first_name=first_name)
    session.add(user)
    session.commit()
    return user

def get_all_items(session: Session, item_type: ItemType = None):
    query = session.query(GameItem)
    if item_type:
        query = query.filter(GameItem.item_type == item_type)
    return query.all()

def get_item_by_id(session: Session, item_id: int):
    return session.query(GameItem).filter(GameItem.id == item_id).first()

def get_inventory_item(session: Session, user_id: int, item_id: int):
    return session.query(Inventory).filter(Inventory.user_id == user_id, Inventory.item_id == item_id).first()

def add_to_inventory(session: Session, user_id: int, item_id: int, quantity: int = 1):
    inv_item = get_inventory_item(session, user_id, item_id)
    if inv_item:
        inv_item.quantity += quantity
    else:
        inv_item = Inventory(user_id=user_id, item_id=item_id, quantity=quantity)
        session.add(inv_item)
    session.commit()
    return inv_item

def get_user_inventory(session: Session, user_id: int):
    return session.query(Inventory).join(GameItem).filter(Inventory.user_id == user_id).all()

def get_market_listings(session: Session):
    return session.query(MarketListing).join(GameItem).all()

def create_market_listing(session: Session, seller_id: int, item_id: int, quantity: int, price: int):
    listing = MarketListing(seller_id=seller_id, item_id=item_id, quantity=quantity, price_diamonds=price)
    session.add(listing)
    session.commit()
    return listing

def get_listing_by_id(session: Session, listing_id: int):
    return session.query(MarketListing).filter(MarketListing.id == listing_id).first()

def delete_listing(session: Session, listing_id: int):
    listing = get_listing_by_id(session, listing_id)
    if listing:
        session.delete(listing)
        session.commit()
        return True
    return False

def get_achievements(session: Session):
    return session.query(Achievement).all()

def get_user_achievements(session: Session, user_id: int):
    return session.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()

def unlock_achievement(session: Session, user_id: int, achievement_id: int):
    ua = UserAchievement(user_id=user_id, achievement_id=achievement_id)
    session.add(ua)
    session.commit()
    return ua

def get_user_quests(session: Session, user_id: int):
    return session.query(UserQuest).filter(UserQuest.user_id == user_id, UserQuest.completed == False).all()

def update_quest_progress(session: Session, user_id: int, quest_type: str, amount: int):
    quests = session.query(UserQuest).filter(UserQuest.user_id == user_id, UserQuest.quest_type == quest_type, UserQuest.completed == False).all()
    for quest in quests:
        quest.progress += amount
        if quest.progress >= quest.goal:
            quest.completed = True
    session.commit()

def get_promo_code(session: Session, code: str):
    return session.query(PromoCode).filter(PromoCode.code == code).first()

def has_used_promo(session: Session, user_id: int, code_id: int):
    return session.query(UsedPromo).filter(UsedPromo.user_id == user_id, UsedPromo.code_id == code_id).first() is not None

def use_promo(session: Session, user_id: int, promo: PromoCode):
    used = UsedPromo(user_id=user_id, code_id=promo.id)
    promo.current_uses += 1
    session.add(used)
    session.commit()

def get_top_players(session: Session, limit: int = 10):
    return session.query(User).order_by(User.coins.desc()).limit(limit).all()
