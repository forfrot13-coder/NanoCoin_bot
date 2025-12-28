from datetime import datetime, timedelta

def get_time_remaining(expiry_time: datetime):
    if not expiry_time:
        return None
    
    delta = expiry_time - datetime.now()
    if delta.total_seconds() <= 0:
        return None
    
    minutes, seconds = divmod(int(delta.total_seconds()), 60)
    return f"{minutes:02d}:{seconds:02d}"

def is_admin(user_id: int, admin_ids: list):
    return user_id in admin_ids
