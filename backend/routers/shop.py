from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from database.connection import get_session
from backend.auth import get_current_user
from backend.services.shop_service import ShopService
from backend.schemas.shop import GameItemSchema, InventoryItemSchema, BuyItemRequest, ToggleItemRequest

router = APIRouter(prefix="/api/shop", tags=["shop"])


@router.get("/items", response_model=List[GameItemSchema])
async def get_shop_items(
    session: Session = Depends(get_session)
):
    """Get all items available in shop."""
    items = ShopService.get_all_items(session)
    return items


@router.post("/buy")
async def buy_item(
    request: BuyItemRequest,
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Buy an item from shop."""
    user_id = user['user_id']
    
    success, error = ShopService.buy_item(session, user_id, request.item_id, request.quantity)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {"success": True, "message": "آیتم با موفقیت خریداری شد"}


@router.get("/inventory", response_model=List[InventoryItemSchema])
async def get_inventory(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's inventory."""
    user_id = user['user_id']
    
    inventory = ShopService.get_user_inventory(session, user_id)
    return inventory


@router.post("/toggle-item")
async def toggle_item(
    request: ToggleItemRequest,
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Toggle item active/inactive in inventory."""
    user_id = user['user_id']
    
    success, error = ShopService.toggle_item_active(
        session, user_id, request.inventory_id, request.active
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {"success": True}


@router.post("/sell/{inventory_id}")
async def sell_item(
    inventory_id: int,
    quantity: int = 1,
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Sell an item from inventory."""
    user_id = user['user_id']
    
    success, error = ShopService.sell_item(session, user_id, inventory_id, quantity)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {"success": True, "message": "آیتم با موفقیت فروخته شد"}
