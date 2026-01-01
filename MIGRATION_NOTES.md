# 📝 Migration Notes - From Bot to Web App

This document helps developers understand what changed and how to work with the new architecture.

---

## 🔄 What Changed?

### Before (v1.0)
```python
# handlers/game.py
async def click_handler(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    # Game logic here...
    await query.edit_message_text("You clicked!")
```

### After (v2.0)
```python
# backend/routers/game.py
@router.post("/api/game/click")
async def click(user: Dict = Depends(get_current_user)):
    user_id = user['user_id']
    # Game logic in service layer
    result = GameService.process_click(...)
    return ClickResponse(**result)
```

```javascript
// webapp/js/game.js
async handleClick() {
    const result = await api.click();
    this.updateUI();
    showToast('Click successful!');
}
```

---

## 📋 File Mapping

### Old → New Structure

| Old Location | New Location | Purpose |
|-------------|--------------|---------|
| `handlers/game.py` | `backend/routers/game.py` + `backend/services/game_service.py` | Game logic |
| `handlers/shop.py` | `backend/routers/shop.py` + `backend/services/shop_service.py` | Shop logic |
| `handlers/start.py` | `bot/main.py` | Bot launcher |
| `utils/game_logic.py` | `backend/services/game_service.py` | Game mechanics |
| `utils/keyboards.py` | `webapp/index.html` | UI elements |
| `utils/formatters.py` | `webapp/js/utils.js` | Formatting |

### What Was Removed

- ❌ `handlers/` - Most handlers removed (kept only start in bot)
- ❌ `utils/keyboards.py` - Inline keyboards replaced with Web App UI
- ❌ `utils/formatters.py` - Text formatting moved to frontend

### What Was Added

- ✅ `bot/main.py` - New simple bot launcher
- ✅ `backend/` - Complete FastAPI backend
- ✅ `webapp/` - Frontend Web App
- ✅ `backend/auth.py` - Telegram WebApp authentication
- ✅ `backend/services/` - Business logic layer

---

## 🔐 Authentication Migration

### Old Way
```python
# In handler
async def some_handler(update: Update, context):
    user_id = update.effective_user.id  # Direct access
    # ... use user_id
```

**Problem:** Client could be spoofed, no verification

### New Way
```python
# In API endpoint
@router.post("/api/endpoint")
async def endpoint(user: Dict = Depends(get_current_user)):
    user_id = user['user_id']  # Verified by HMAC-SHA256
    # ... use user_id safely
```

**Benefits:** 
- Cryptographically verified
- Cannot be spoofed
- Automatic authentication on all endpoints

---

## 🎮 Game Logic Migration

### Click System

**Old:**
```python
# handlers/game.py
async def click_handler(update, context):
    user = get_user(session, user_id)
    if user.energy <= 0:
        await query.answer("No energy!")
        return
    
    user.coins += calculate_reward(user)
    user.energy -= 1
    session.commit()
    
    await query.edit_message_text(f"Coins: {user.coins}")
```

**New:**
```python
# backend/services/game_service.py
class GameService:
    @staticmethod
    def process_click(user: User, session: Session):
        if user.energy <= 0:
            return None, "No energy"
        
        reward = GameService.calculate_click_reward(user, session)
        user.coins += reward
        user.energy -= 1
        
        return {"coins_earned": reward, ...}, None

# backend/routers/game.py
@router.post("/api/game/click")
async def click(user: Dict = Depends(get_current_user), session = Depends(get_session)):
    db_user = session.query(User).filter(User.user_id == user['user_id']).first()
    result, error = GameService.process_click(db_user, session)
    if error:
        raise HTTPException(400, error)
    session.commit()
    return result
```

```javascript
// webapp/js/game.js
async handleClick() {
    const result = await api.click();
    this.userData.coins = result.new_coins;
    this.userData.energy = result.new_energy;
    this.updateUI();
    showCoinPopup(result.coins_earned);
}
```

**Benefits:**
- Clean separation of concerns
- Testable business logic
- Reusable services
- Better error handling

---

## 🏪 Shop Migration

### Old Approach
```python
# handlers/shop.py
@router.callback_query(pattern="^shop_buy_")
async def shop_buy(update, context):
    query = update.callback_query
    item_id = int(query.data.split("_")[2])
    
    # Buy logic
    # Update database
    
    await query.edit_message_text("Item purchased!")
    await query.answer()
```

### New Approach
```python
# backend/routers/shop.py
@router.post("/api/shop/buy")
async def buy_item(
    request: BuyItemRequest,
    user: Dict = Depends(get_current_user),
    session = Depends(get_session)
):
    success, error = ShopService.buy_item(
        session, user['user_id'], request.item_id, request.quantity
    )
    if error:
        raise HTTPException(400, error)
    session.commit()
    return {"success": True}
```

```javascript
// webapp/js/shop.js
async buyItem(itemId) {
    await api.buyItem(itemId, 1);
    showToast('Item purchased!');
    await this.loadShop();
    await gameManager.refreshProfile();
}
```

---

## 🔄 Database Queries

### Before
```python
# In handler directly
user = session.query(User).filter(User.user_id == user_id).first()
user.coins += 100
session.commit()
```

### After
```python
# In service layer
class GameService:
    @staticmethod
    def add_coins(session: Session, user_id: int, amount: int):
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False, "User not found"
        user.coins += amount
        return True, None

# In router
@router.post("/api/user/add-coins")
async def add_coins(amount: int, user = Depends(get_current_user), session = Depends(get_session)):
    success, error = GameService.add_coins(session, user['user_id'], amount)
    if error:
        raise HTTPException(400, error)
    session.commit()
    return {"success": True}
```

---

## 🎨 UI Migration

### Inline Keyboards → Web App UI

**Old:**
```python
keyboard = [
    [InlineKeyboardButton("Click", callback_data="game_click")],
    [InlineKeyboardButton("Mine", callback_data="game_mine")],
    [InlineKeyboardButton("Shop", callback_data="shop_main")]
]
```

**New:**
```html
<!-- webapp/index.html -->
<button id="click-btn" class="click-button">
    <span class="click-icon">🪙</span>
</button>

<button id="claim-mining-btn">
    💰 Claim Mining Rewards
</button>

<nav class="bottom-nav">
    <button data-screen="main-screen">Game</button>
    <button data-screen="shop-screen">Shop</button>
</nav>
```

```javascript
// webapp/js/app.js
document.getElementById('click-btn').addEventListener('click', () => {
    gameManager.handleClick();
});
```

---

## 📡 API Communication

### Request/Response Flow

```
User Action (Frontend)
    ↓
JavaScript API Call
    ↓
HTTPS Request with Bearer Token (initData)
    ↓
FastAPI Backend
    ↓
Auth Validation (HMAC-SHA256)
    ↓
Service Layer (Business Logic)
    ↓
Database Operation
    ↓
Response (JSON)
    ↓
Frontend Updates UI
```

### Example Full Flow

**1. User clicks coin button:**
```javascript
// webapp/js/game.js
document.getElementById('click-btn').addEventListener('click', async () => {
    const result = await api.click();
    // Update UI with result
});
```

**2. API client sends request:**
```javascript
// webapp/js/api.js
async click() {
    return this.call('/api/game/click', 'POST');
}

async call(endpoint, method, data) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
        method,
        headers: {
            'Authorization': `Bearer ${this.initData}`,  // Telegram initData
            'Content-Type': 'application/json'
        },
        body: data ? JSON.stringify(data) : null
    });
    return response.json();
}
```

**3. Backend validates and processes:**
```python
# backend/routers/game.py
@router.post("/api/game/click")
async def click(
    user: Dict = Depends(get_current_user),  # Auth happens here
    session: Session = Depends(get_session)
):
    db_user = session.query(User).filter(User.user_id == user['user_id']).first()
    result, error = GameService.process_click(db_user, session)
    if error:
        raise HTTPException(400, error)
    session.commit()
    return ClickResponse(success=True, **result)
```

**4. Service handles logic:**
```python
# backend/services/game_service.py
class GameService:
    @staticmethod
    def process_click(user: User, session: Session):
        if user.energy <= 0:
            return None, "No energy"
        
        reward = GameService.calculate_click_reward(user, session)
        user.coins += reward
        user.energy -= 1
        
        return {
            "coins_earned": reward,
            "new_energy": user.energy,
            "new_coins": user.coins,
            ...
        }, None
```

---

## 🧪 Testing

### Old Way
```python
# Manual testing through Telegram bot
# Hard to automate
```

### New Way
```python
# backend/tests/test_game.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_click_endpoint():
    # Mock auth
    response = client.post("/api/game/click", headers={
        "Authorization": "Bearer mock_init_data"
    })
    assert response.status_code == 200
    assert "coins_earned" in response.json()
```

```javascript
// webapp/tests/game.test.js (if using Jest)
test('click increases coins', async () => {
    const result = await api.click();
    expect(result.success).toBe(true);
    expect(result.coins_earned).toBeGreaterThan(0);
});
```

---

## ⚠️ Common Pitfalls

### 1. Trusting Client Data
❌ **Wrong:**
```javascript
// Frontend
const coins = 1000000;  // User changed this
api.updateCoins(coins);  // NEVER DO THIS
```

✅ **Correct:**
```python
# Backend calculates everything
reward = calculate_reward(user)
user.coins += reward
```

### 2. Not Using Services
❌ **Wrong:**
```python
# In router directly
@router.post("/click")
async def click(session):
    user = session.query(User)...
    user.coins += 100  # Logic in router
```

✅ **Correct:**
```python
# Router calls service
@router.post("/click")
async def click(session):
    result = GameService.process_click(user, session)
    return result
```

### 3. Forgetting Authentication
❌ **Wrong:**
```python
@router.get("/user/{user_id}")
async def get_user(user_id: int):  # Anyone can access any user!
```

✅ **Correct:**
```python
@router.get("/user/profile")
async def get_profile(user: Dict = Depends(get_current_user)):
    # Only authenticated user
```

---

## 📚 Additional Resources

- [Telegram Web Apps Documentation](https://core.telegram.org/bots/webapps)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)

---

## 🎯 Migration Checklist for Your Features

When migrating a new feature:

- [ ] Create service in `backend/services/`
- [ ] Create router in `backend/routers/`
- [ ] Create Pydantic schemas in `backend/schemas/`
- [ ] Add frontend UI in `webapp/`
- [ ] Add API calls in `webapp/js/api.js`
- [ ] Add logic in appropriate JS manager
- [ ] Test authentication
- [ ] Test error handling
- [ ] Update documentation

---

**Remember:** The bot is now ONLY a launcher. All game logic is in the backend. All UI is in the webapp.
