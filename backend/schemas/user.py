from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    coins: int
    diamonds: int
    energy: int
    max_energy: int
    electricity: int
    max_electricity: int
    click_level: int
    click_xp: int
    active_boost_until: Optional[datetime]
    boost_multiplier: float
    daily_streak: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    coins: int
    click_level: int
    rank: int

    class Config:
        from_attributes = True
