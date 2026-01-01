from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GameItemSchema(BaseModel):
    id: int
    name: str
    item_code: str
    item_type: str
    emoji: str
    price_diamonds: int
    sell_price: int
    stock: int
    mining_rate: float
    electricity_consumption: float
    buff_click_coins: int
    buff_mining_speed: float
    buff_luck: float

    class Config:
        from_attributes = True


class InventoryItemSchema(BaseModel):
    id: int
    item: GameItemSchema
    quantity: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BuyItemRequest(BaseModel):
    item_id: int
    quantity: int = 1


class ToggleItemRequest(BaseModel):
    inventory_id: int
    active: bool
