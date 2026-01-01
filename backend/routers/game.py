from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from database.connection import get_session
from database.models import User
from backend.auth import get_current_user
from backend.services.game_service import GameService
from backend.schemas.game import ClickResponse, MineResponse, RefillEnergyRequest, ActivateBoostRequest

router = APIRouter(prefix="/api/game", tags=["game"])


@router.post("/click", response_model=ClickResponse)
async def click(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Process a click action."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result, error = GameService.process_click(db_user, session)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return ClickResponse(
        success=True,
        **result
    )


@router.post("/mine", response_model=MineResponse)
async def mine(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Claim mining rewards."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result, error = GameService.claim_mining_rewards(db_user, session)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return MineResponse(
        success=True,
        **result
    )


@router.post("/refill-energy")
async def refill_energy(
    request: RefillEnergyRequest,
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Refill energy using diamonds."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success, error = GameService.refill_energy(db_user, request.amount)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {
        "success": True,
        "new_energy": db_user.energy,
        "new_diamonds": db_user.diamonds
    }


@router.post("/activate-boost")
async def activate_boost(
    request: ActivateBoostRequest,
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Activate click boost."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success, error = GameService.activate_boost(db_user, request.duration_minutes)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {
        "success": True,
        "active_until": db_user.active_boost_until,
        "new_diamonds": db_user.diamonds
    }


@router.post("/daily-reward")
async def claim_daily_reward(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Claim daily reward."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result, error = GameService.claim_daily_reward(db_user, session)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    session.commit()
    
    return {
        "success": True,
        **result
    }
