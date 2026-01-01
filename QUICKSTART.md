# ⚡️ Quick Start Guide - NanoCoin Web App

Get your NanoCoin game running in 5 minutes!

---

## 📋 Prerequisites

- Python 3.10 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Your Telegram User ID (get from [@userinfobot](https://t.me/userinfobot))

---

## 🚀 Installation (5 Steps)

### Step 1: Clone & Setup
```bash
# Clone the repository (or download ZIP)
cd NanoCoin_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

Set these values in `.env`:
```bash
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=sqlite:///nanocoin.db
WEBAPP_URL=https://your-ngrok-url.ngrok.io/webapp  # See step 4
```

### Step 3: Verify Setup
```bash
# Run verification script
python test_setup.py
```

Should see all ✅ checks passing.

### Step 4: Start ngrok (for local testing)
```bash
# In a new terminal
ngrok http 8000

# Copy the HTTPS URL (looks like: https://abc123.ngrok.io)
# Update WEBAPP_URL in .env with this URL + /webapp
# Example: WEBAPP_URL=https://abc123.ngrok.io/webapp
```

**Important:** Telegram requires HTTPS for Web Apps. ngrok provides free HTTPS tunneling for testing.

### Step 5: Run the Application
```bash
# Terminal 1: Start Backend API
python -m backend.main

# Terminal 2: Start Telegram Bot
python -m bot.main
```

---

## 🎮 Test It!

1. Open Telegram
2. Find your bot (search for bot username)
3. Send `/start`
4. Click "🎮 بازی کن!" button
5. **Game opens in Web App!** 🎉

---

## 🎯 What You Should See

### In Terminal 1 (Backend):
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### In Terminal 2 (Bot):
```
Bot started - Telegram Web App launcher mode
```

### In Telegram:
- Bot responds to `/start`
- Shows "🎮 بازی کن!" button
- Clicking opens full-screen game interface

---

## 🐛 Troubleshooting

### "Web App doesn't open"
**Solution:** Check `WEBAPP_URL` in `.env` - must be HTTPS with `/webapp` at the end

### "Authentication Failed" error in game
**Solution:** 
1. Make sure `BOT_TOKEN` is correct in `.env`
2. Restart both terminals
3. Try refreshing the Web App

### "Database Error"
**Solution:**
```bash
# Delete old database
rm nanocoin.db
# Restart backend - it will recreate tables
python -m backend.main
```

### "Module not found" errors
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📱 Testing on Mobile

1. Open Telegram app on your phone
2. Search for your bot
3. Send `/start`
4. Click button - game opens full-screen
5. **Best experience on mobile!**

---

## 🔄 Making Changes

### Update game logic:
```bash
# Edit files in backend/services/
nano backend/services/game_service.py

# Restart backend
# Press Ctrl+C in Terminal 1, then:
python -m backend.main
```

### Update UI:
```bash
# Edit files in webapp/
nano webapp/css/styles.css
nano webapp/js/game.js

# Refresh Web App in Telegram
# (Pull down to refresh or close and reopen)
```

### Update bot messages:
```bash
# Edit bot/main.py
nano bot/main.py

# Restart bot
# Press Ctrl+C in Terminal 2, then:
python -m bot.main
```

---

## 🎨 Customization Ideas

### Change colors:
Edit `webapp/css/styles.css`:
```css
:root {
    --primary-color: #3390ec;  /* Change this */
    --bg-color: #1a1a2e;       /* Change this */
}
```

### Add new game feature:
1. Create service: `backend/services/my_service.py`
2. Create router: `backend/routers/my_feature.py`
3. Add to `backend/main.py`:
```python
from backend.routers import my_feature
app.include_router(my_feature.router)
```
4. Add UI in `webapp/index.html`
5. Add JS in `webapp/js/my_feature.js`

### Change bot language:
Edit `bot/main.py`:
```python
welcome_message = "Welcome to NanoCoin!"  # Change to any language
```

---

## 📊 Check Database

```bash
# Install SQLite browser (optional)
sudo apt install sqlitebrowser  # Linux
brew install sqlitebrowser      # Mac

# Open database
sqlitebrowser nanocoin.db

# Or use Python
python
>>> from database.connection import get_session
>>> from database.models import User
>>> session = get_session()
>>> users = session.query(User).all()
>>> print(f"Total users: {len(users)}")
```

---

## 🚀 Deploy to Production

Once everything works locally, see:
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
- [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md) - Architecture details

Quick options:
1. **Docker:** `docker-compose up -d`
2. **VPS:** Follow systemd setup in DEPLOYMENT.md
3. **Render.com:** Push to GitHub, connect, deploy

---

## 📚 Next Steps

1. ✅ Get it running locally (you just did this!)
2. 📖 Read [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md) to understand architecture
3. 🎨 Customize colors and text
4. 🔧 Add your own features
5. 🚀 Deploy to production
6. 📱 Share with users!

---

## 🆘 Need Help?

### Common Commands

```bash
# Stop everything: Press Ctrl+C in both terminals

# Check if backend is running:
curl http://localhost:8000/health

# Check database:
ls -lh nanocoin.db

# View backend logs:
# (They appear in Terminal 1)

# View bot logs:
# (They appear in Terminal 2)

# Reset everything:
rm nanocoin.db
# Restart both terminals
```

### Documentation

- [README.md](./README.md) - Project overview
- [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md) - Complete architecture guide  
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) - Code migration details

### Online Resources

- [Telegram Web Apps Docs](https://core.telegram.org/bots/webapps)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Python Telegram Bot](https://docs.python-telegram-bot.org/)

---

## ✅ Success Checklist

After following this guide, you should have:

- [x] Backend API running on http://localhost:8000
- [x] Bot running and responding to /start
- [x] Web App opening in Telegram
- [x] Ability to click and earn coins
- [x] Shop, inventory, and leaderboard working
- [x] Understanding of how to make changes

**Congratulations! Your Telegram Web App game is live!** 🎉

---

**Next:** Try clicking around, buying items from shop, and exploring all features. Then check out the other guides to learn more and deploy to production.
