import hmac
import hashlib
import json
from urllib.parse import parse_qs, unquote
from typing import Optional, Dict
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import BOT_TOKEN

security = HTTPBearer()


def validate_telegram_webapp_data(init_data: str) -> Optional[Dict]:
    """
    Validate Telegram Web App initData using HMAC-SHA256.
    
    According to Telegram documentation:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Args:
        init_data: The initData string from Telegram Web App
        
    Returns:
        Dict with validated user data or None if invalid
    """
    try:
        # Parse the init_data
        parsed = parse_qs(init_data)
        
        # Extract hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            return None
        
        # Remove hash from data for validation
        data_check_string_parts = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                value = parsed[key][0]
                data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Create secret key
        secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate expected hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash != received_hash:
            return None
        
        # Parse user data
        user_data = json.loads(unquote(parsed.get('user', ['{}'])[0]))
        
        # Add auth_date for token expiry checking
        auth_date = int(parsed.get('auth_date', [0])[0])
        
        return {
            'user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'language_code': user_data.get('language_code'),
            'auth_date': auth_date
        }
    except Exception as e:
        print(f"Error validating Telegram data: {e}")
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    """
    FastAPI dependency to get current authenticated user from Telegram Web App.
    
    Usage in endpoints:
        @app.get("/api/user/profile")
        async def get_profile(user: Dict = Depends(get_current_user)):
            user_id = user['user_id']
            ...
    """
    token = credentials.credentials
    
    # Validate Telegram initData
    user_data = validate_telegram_webapp_data(token)
    
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    
    # Check if auth_date is not too old (e.g., 24 hours)
    import time
    current_time = int(time.time())
    if current_time - user_data['auth_date'] > 86400:  # 24 hours
        raise HTTPException(
            status_code=401,
            detail="Authentication expired"
        )
    
    return user_data


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)) -> Optional[Dict]:
    """
    Optional authentication - returns None if no credentials provided.
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


def is_admin(user: Dict) -> bool:
    """Check if user is admin."""
    from backend.config import ADMIN_IDS
    return user['user_id'] in ADMIN_IDS


def require_admin(user: Dict = Security(get_current_user)) -> Dict:
    """FastAPI dependency to require admin access."""
    if not is_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user
