from pydantic import BaseModel
from typing import Optional


class ClickResponse(BaseModel):
    success: bool
    coins_earned: int
    leveled_up: bool
    diamond_found: bool
    new_energy: int
    new_coins: int
    new_diamonds: int
    new_level: Optional[int] = None


class MineResponse(BaseModel):
    success: bool
    coins_earned: int
    electricity_spent: int
    diamonds_earned: int
    new_electricity: int
    new_coins: int
    new_diamonds: int


class RefillEnergyRequest(BaseModel):
    amount: int = 50


class ActivateBoostRequest(BaseModel):
    duration_minutes: int = 15
