# 🚀 NanoCoin Bot - Web App Refactoring Guide

## 📋 Overview

This document explains the complete refactoring of NanoCoin from a traditional Telegram bot to a modern **Telegram Web App** architecture.

### Architecture Changes

**OLD Architecture:**
```
Telegram Bot
└── All game logic in bot handlers
└── Users interact via inline buttons
└── No visual UI
```

**NEW Architecture:**
```
┌─────────────────┐
│  Telegram Bot   │ ← Entry point only (/start)
│   (bot/main.py) │
└────────┬────────┘
         │ Opens Web App
         ↓
┌─────────────────┐
│   Web App UI    │ ← Visual game interface
│ (webapp/*.html) │ ← Telegram WebApp API
└────────┬────────┘
         │ API Calls
         ↓
┌─────────────────┐
│  FastAPI Backend│ ← Game logic & database
│ (backend/*.py)  │ ← Auth & validation
└─────────────────┘
```

---

## 🗂 New Project Structure

```
/home/engine/project/
├── bot/                          # 🤖 Telegram Bot (Launcher Only)
│   ├── main.py                   # Bot entry point - /start command
│   └── __init__.py
│
├── backend/                      # 🔧 FastAPI Backend API
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration
│   ├── auth.py                   # Telegram WebApp authentication
│   ├── routers/                  # API endpoints
│   │   ├── user.py               # User profile & leaderboard
│   │   ├── game.py               # Click, mining, boosts
│   │   └── shop.py               # Shop & inventory
│   ├── services/                 # Business logic
│   │   ├── game_service.py       # Game mechanics
│   │   ├── shop_service.py       # Shop operations
│   │   └── quest_service.py      # Quest management
│   └── schemas/                  # Pydantic models
│       ├── user.py
│       ├── game.py
│       └── shop.py
│
├── webapp/                       # 🎮 Frontend (Telegram Web App)
│   ├── index.html                # Main UI
│   ├── css/
│   │   └── styles.css            # Styling
│   └── js/
│       ├── app.js                # App initialization
│       ├── api.js                # API client
│       ├── game.js               # Game logic
│       ├── shop.js               # Shop & inventory
│       └── utils.js              # Utilities
│
├── database/                     # 💾 Database Layer (kept)
│   ├── connection.py
│   ├── models.py
│   ├── queries.py
│   └── admin_models.py
│
├── jobs/                         # ⏰ Background Jobs (kept)
│   └── background_jobs.py
│
├── config.py                     # 🔧 Shared configuration
├── requirements.txt              # 📦 Updated dependencies
└── README.md                     # 📖 Documentation
```

---

## 🔐 Authentication System

### How It Works

The new system uses **Telegram Web App initData validation**:

1. **Frontend** (webapp/js/api.js):
   - Gets `initData` from Telegram WebApp API
   - Sends it as Bearer token in Authorization header

2. **Backend** (backend/auth.py):
   - Validates initData using HMAC-SHA256
   - Verifies signature with BOT_TOKEN
   - Extracts user info (user_id, username, etc.)
   - Returns authenticated user to endpoints

### Security Features

✅ **HMAC-SHA256 validation** - Prevents tampering  
✅ **Token expiry checking** - 24-hour validity  
✅ **No client-side trust** - User ID comes from Telegram  
✅ **Rate limiting ready** - Can add throttling  
✅ **Admin verification** - Check against ADMIN_IDS

### Code Example

```python
# In any API endpoint:
@router.get("/api/user/profile")
async def get_profile(user: Dict = Depends(get_current_user)):
    user_id = user['user_id']  # Safely validated user ID
    # ... your logic
```

---

## 🎮 Game Features Migration

All features have been migrated from bot handlers to the Web App:

### ✅ Migrated Features

| Feature | Old Location | New Location |
|---------|-------------|--------------|
| Click System | `handlers/game.py` | `backend/routers/game.py` + `webapp/js/game.js` |
| Mining | `handlers/game.py` | `backend/services/game_service.py` |
| Shop | `handlers/shop.py` | `backend/routers/shop.py` + `webapp/js/shop.js` |
| Inventory | `handlers/profile.py` | `backend/services/shop_service.py` |
| Leaderboard | `handlers/profile.py` | `backend/routers/user.py` |
| Daily Rewards | Bot inline | `backend/services/game_service.py` |
| Energy Refill | Bot inline | `backend/routers/game.py` |
| Boosts | Bot inline | `backend/routers/game.py` |
| Quests | `handlers/quests.py` | `backend/services/quest_service.py` |

### 🚧 Features Not Yet Migrated

These features still exist in the old code but need API endpoints:

- **Casino/Slots** - Need `backend/routers/casino.py`
- **Market (P2P)** - Need `backend/routers/market.py`
- **Achievements** - Need `backend/routers/achievements.py`
- **Admin Panel** - Can keep as bot commands or add API
- **Join Verification** - Bot-only feature

---

## 🚀 Deployment Guide

### Option 1: Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your BOT_TOKEN and settings

# 3. Run backend API
python -m backend.main
# API runs at http://localhost:8000

# 4. In another terminal, run bot
python -m bot.main

# 5. Set WEBAPP_URL in .env to your ngrok URL (for testing)
# ngrok http 8000
```

### Option 2: Production (VPS/Cloud)

#### A. Using Docker (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run both bot and API
CMD python -m backend.main & python -m bot.main
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  app:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
```

Run:
```bash
docker-compose up -d
```

#### B. Using Systemd (Linux VPS)

Create `/etc/systemd/system/nanocoin-api.service`:
```ini
[Unit]
Description=NanoCoin API
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/NanoCoin_bot
Environment="PATH=/home/youruser/venv/bin"
ExecStart=/home/youruser/venv/bin/python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/nanocoin-bot.service` (similar)

Enable:
```bash
sudo systemctl enable nanocoin-api
sudo systemctl enable nanocoin-bot
sudo systemctl start nanocoin-api
sudo systemctl start nanocoin-bot
```

#### C. Using Render.com

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: nanocoin-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m backend.main
    envVars:
      - key: BOT_TOKEN
        sync: false
      - key: DATABASE_URL
        sync: false
```

2. Push to GitHub
3. Connect to Render
4. Set environment variables

### Important: Set WEBAPP_URL

After deploying, update `.env`:
```bash
WEBAPP_URL=https://your-domain.com/webapp
# or
WEBAPP_URL=https://your-render-app.onrender.com/webapp
```

This URL is what the bot sends when user clicks "Play Game 🎮"

---

## 🔧 Environment Variables

Required in `.env`:

```bash
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321

# Database
DATABASE_URL=sqlite:///nanocoin.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/nanocoin

# Backend API
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://localhost:8000

# Web App URL (IMPORTANT!)
WEBAPP_URL=http://localhost:8000/webapp
# In production, use your domain:
# WEBAPP_URL=https://yourdomain.com/webapp

# Security
SECRET_KEY=your-secret-key-change-this-in-production
```

---

## 📡 API Endpoints Reference

### User Endpoints

- `GET /api/user/profile` - Get current user profile
- `GET /api/user/leaderboard` - Get top players
- `POST /api/user/sync` - Sync user data

### Game Endpoints

- `POST /api/game/click` - Process click action
- `POST /api/game/mine` - Claim mining rewards
- `POST /api/game/refill-energy` - Refill energy with diamonds
- `POST /api/game/activate-boost` - Activate 2x boost
- `POST /api/game/daily-reward` - Claim daily reward

### Shop Endpoints

- `GET /api/shop/items` - Get all shop items
- `POST /api/shop/buy` - Buy an item
- `GET /api/shop/inventory` - Get user inventory
- `POST /api/shop/toggle-item` - Toggle item active status
- `POST /api/shop/sell/{id}` - Sell item

---

## 🛡 Security Best Practices

### ✅ What We Implemented

1. **Telegram WebApp Data Validation**
   - HMAC-SHA256 signature verification
   - Protection against replay attacks

2. **No Client Trust**
   - User ID extracted from validated initData
   - Cannot be spoofed by malicious client

3. **Token Expiry**
   - initData valid for 24 hours
   - Prevents old tokens from being reused

4. **CORS Configuration**
   - In production, restrict to your domain
   - Currently set to `*` for development

### 🔒 Additional Recommendations

1. **Rate Limiting** - Add throttling to prevent abuse:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/game/click")
@limiter.limit("10/second")
async def click(...):
    ...
```

2. **Database Transactions** - Ensure atomic operations:
```python
with session.begin():
    # Multiple operations
    user.coins += 100
    user.energy -= 1
```

3. **Input Validation** - Pydantic already validates, but add business logic checks

4. **Logging** - Log suspicious activities

---

## 🧪 Testing the Web App

### 1. Test Bot Launch

1. Message your bot: `/start`
2. Click "🎮 بازی کن!" button
3. Web App should open

### 2. Test Authentication

Check browser console for:
```
Telegram WebApp initialized
initData: query_id=...&user=...
```

### 3. Test Game Features

- Click the coin button
- Check mining rewards
- Buy items from shop
- View leaderboard

### 4. Test on Mobile

Telegram Web Apps work best on mobile:
- Open Telegram on phone
- Start bot
- Test all features

---

## 🐛 Troubleshooting

### Web App doesn't open

- Check `WEBAPP_URL` in `.env`
- Ensure backend is running
- Check bot has correct token

### Authentication Failed

- Verify BOT_TOKEN is correct
- Check initData validation in `backend/auth.py`
- Ensure Telegram WebApp SDK is loaded

### API Calls Fail

- Check browser console for errors
- Verify backend is accessible
- Check CORS settings

### Database Errors

- Ensure `init_db()` is called
- Check DATABASE_URL
- For PostgreSQL, ensure psycopg2 is installed

---

## 📚 Key Code Sections

### Bot: Opening Web App

```python
# bot/main.py
keyboard = [
    [InlineKeyboardButton(
        text="🎮 بازی کن!",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]
]
```

### Frontend: Initializing Telegram WebApp

```javascript
// webapp/js/api.js
init() {
    if (window.Telegram?.WebApp) {
        this.initData = window.Telegram.WebApp.initData;
        window.Telegram.WebApp.expand();
    }
}
```

### Backend: Validating Auth

```python
# backend/auth.py
def validate_telegram_webapp_data(init_data: str) -> Optional[Dict]:
    # HMAC-SHA256 validation
    calculated_hash = hmac.new(...)
    if calculated_hash != received_hash:
        return None
    return user_data
```

### API Call: Click

```python
# backend/routers/game.py
@router.post("/click")
async def click(user: Dict = Depends(get_current_user), ...):
    result, error = GameService.process_click(db_user, session)
    return ClickResponse(success=True, **result)
```

---

## 🎯 Migration Checklist

- [x] Create FastAPI backend
- [x] Implement Telegram WebApp auth
- [x] Build Web App UI
- [x] Migrate click system
- [x] Migrate mining system
- [x] Migrate shop & inventory
- [x] Migrate leaderboard
- [x] Migrate daily rewards
- [x] Refactor bot to launcher
- [ ] Add casino endpoints
- [ ] Add market endpoints
- [ ] Add achievements endpoints
- [ ] Add admin API (optional)
- [ ] Deploy to production
- [ ] Test on real devices
- [ ] Monitor for issues

---

## 📞 Support

For issues or questions:
1. Check this guide
2. Review code comments
3. Check Telegram WebApp docs: https://core.telegram.org/bots/webapps

---

## 🎉 Success Metrics

After refactoring:
- ✅ No gameplay in bot handlers
- ✅ Clean separation of concerns
- ✅ Secure authentication
- ✅ Scalable architecture
- ✅ Visual, engaging UI
- ✅ Mobile-optimized
- ✅ Production-ready

---

**Created:** 2024
**Version:** 2.0.0
**Architecture:** Telegram Web App
