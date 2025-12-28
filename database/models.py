from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import datetime
import enum

class Base(DeclarativeBase):
    pass

class ItemType(enum.Enum):
    MINER = "MINER"
    BUFF = "BUFF"
    SKIN = "SKIN"
    AVATAR = "AVATAR"
    ENERGY = "ENERGY"

class QuestType(enum.Enum):
    CLICK = "CLICK"
    MINE = "MINE"

class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    coins = Column(BigInteger, default=0)
    diamonds = Column(Integer, default=0)
    energy = Column(Integer, default=1000)
    max_energy = Column(Integer, default=1000)
    electricity = Column(Integer, default=5000)
    max_electricity = Column(Integer, default=5000)
    click_level = Column(Integer, default=1)
    click_xp = Column(Integer, default=0)
    active_boost_until = Column(DateTime, nullable=True)
    boost_multiplier = Column(Float, default=1.0)
    slot_1_id = Column(Integer, ForeignKey("game_items.id"), nullable=True)
    slot_2_id = Column(Integer, ForeignKey("game_items.id"), nullable=True)
    slot_3_id = Column(Integer, ForeignKey("game_items.id"), nullable=True)
    last_mined_at = Column(DateTime, default=func.now())
    last_daily_claim = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    inventory = relationship("Inventory", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    quests = relationship("UserQuest", back_populates="user")

class GameItem(Base):
    __tablename__ = "game_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    item_code = Column(String, unique=True, nullable=False)
    item_type = Column(Enum(ItemType), nullable=False)
    emoji = Column(String, default="📦")
    price_diamonds = Column(Integer, default=0)
    sell_price = Column(Integer, default=0)
    stock = Column(Integer, default=-1)  # -1 for unlimited
    mining_rate = Column(Float, default=0.0)
    electricity_consumption = Column(Float, default=0.0)
    buff_click_coins = Column(Integer, default=0)
    buff_mining_speed = Column(Float, default=0.0)
    buff_luck = Column(Float, default=0.0)
    miner_diamond_chance = Column(Float, default=0.0)
    can_drop = Column(Boolean, default=False)
    drop_chance = Column(Float, default=0.0)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("game_items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="inventory")
    item = relationship("GameItem")

class MarketListing(Base):
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("game_items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price_diamonds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    seller = relationship("User")
    item = relationship("GameItem")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    emoji = Column(String, default="🏆")
    target_coins = Column(BigInteger, default=0)
    target_diamonds = Column(Integer, default=0)
    target_miners = Column(Integer, default=0)
    reward_coins = Column(BigInteger, default=0)
    reward_diamonds = Column(Integer, default=0)

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    achieved_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class UserQuest(Base):
    __tablename__ = "user_quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    quest_type = Column(Enum(QuestType), nullable=False)
    goal = Column(BigInteger, default=0)
    progress = Column(BigInteger, default=0)
    reward_coins = Column(BigInteger, default=0)
    reward_diamonds = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    reset_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="quests")

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    reward_coins = Column(BigInteger, default=0)
    reward_diamonds = Column(Integer, default=0)
    max_uses = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    expiry_date = Column(DateTime, nullable=True)

class UsedPromo(Base):
    __tablename__ = "used_promos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    used_at = Column(DateTime, default=func.now())
