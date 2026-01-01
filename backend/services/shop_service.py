from sqlalchemy.orm import Session
from database.models import User, GameItem, Inventory, ItemType
from typing import Tuple, Optional


class ShopService:
    """Service for shop operations."""
    
    @staticmethod
    def get_all_items(session: Session):
        """Get all items available in shop."""
        return session.query(GameItem).all()
    
    @staticmethod
    def get_item_by_id(session: Session, item_id: int):
        """Get specific item by ID."""
        return session.query(GameItem).filter(GameItem.id == item_id).first()
    
    @staticmethod
    def buy_item(session: Session, user_id: int, item_id: int, quantity: int = 1) -> Tuple[bool, Optional[str]]:
        """
        Buy an item from the shop.
        
        Returns:
            Tuple of (success, error_message)
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        item = session.query(GameItem).filter(GameItem.id == item_id).first()
        
        if not user:
            return False, "User not found"
        
        if not item:
            return False, "Item not found"
        
        total_cost = item.price_diamonds * quantity
        
        if user.diamonds < total_cost:
            return False, "الماس کافی ندارید! 💎"
        
        # Check stock
        if item.stock != -1 and item.stock < quantity:
            return False, "موجودی کافی نیست"
        
        # Deduct cost
        user.diamonds -= total_cost
        
        # Update stock
        if item.stock != -1:
            item.stock -= quantity
        
        # Add to inventory
        existing_inv = session.query(Inventory).filter(
            Inventory.user_id == user_id,
            Inventory.item_id == item_id
        ).first()
        
        if existing_inv:
            existing_inv.quantity += quantity
        else:
            new_inv = Inventory(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                is_active=False
            )
            session.add(new_inv)
        
        return True, None
    
    @staticmethod
    def get_user_inventory(session: Session, user_id: int):
        """Get user's inventory."""
        return session.query(Inventory).filter(
            Inventory.user_id == user_id
        ).all()
    
    @staticmethod
    def toggle_item_active(session: Session, user_id: int, inventory_id: int, active: bool) -> Tuple[bool, Optional[str]]:
        """
        Toggle item active status in inventory.
        
        Returns:
            Tuple of (success, error_message)
        """
        inv_item = session.query(Inventory).filter(
            Inventory.id == inventory_id,
            Inventory.user_id == user_id
        ).first()
        
        if not inv_item:
            return False, "Item not found in inventory"
        
        inv_item.is_active = active
        
        return True, None
    
    @staticmethod
    def sell_item(session: Session, user_id: int, inventory_id: int, quantity: int = 1) -> Tuple[bool, Optional[str]]:
        """
        Sell an item from inventory back to shop.
        
        Returns:
            Tuple of (success, error_message)
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        inv_item = session.query(Inventory).filter(
            Inventory.id == inventory_id,
            Inventory.user_id == user_id
        ).first()
        
        if not user:
            return False, "User not found"
        
        if not inv_item:
            return False, "Item not found in inventory"
        
        if inv_item.quantity < quantity:
            return False, "تعداد کافی ندارید"
        
        # Calculate sell price
        sell_price = inv_item.item.sell_price * quantity
        
        # Add coins
        user.coins += sell_price
        
        # Remove from inventory
        inv_item.quantity -= quantity
        
        if inv_item.quantity <= 0:
            session.delete(inv_item)
        
        return True, None
