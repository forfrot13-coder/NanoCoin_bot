from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from database.connection import get_session
from database.models import User
from backend.auth import get_current_user
from backend.schemas.user import UserProfile, LeaderboardEntry

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current user's profile."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        # Create new user
        db_user = User(
            user_id=user_id,
            username=user.get('username'),
            first_name=user.get('first_name')
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    
    return db_user


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Get top players leaderboard."""
    users = session.query(User).order_by(User.coins.desc()).limit(limit).all()
    
    leaderboard = []
    for idx, user in enumerate(users, start=1):
        leaderboard.append(LeaderboardEntry(
            user_id=user.user_id,
            username=user.username,
            first_name=user.first_name,
            coins=user.coins,
            click_level=user.click_level,
            rank=idx
        ))
    
    return leaderboard


@router.post("/sync")
async def sync_user(
    user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Sync user data (useful for energy regeneration, etc)."""
    user_id = user['user_id']
    
    db_user = session.query(User).filter(User.user_id == user_id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Here you could add energy regeneration over time
    # For now just return current state
    
    return {
        "energy": db_user.energy,
        "electricity": db_user.electricity,
        "coins": db_user.coins,
        "diamonds": db_user.diamonds
    }
