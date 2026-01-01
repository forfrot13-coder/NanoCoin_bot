# 🚀 Deployment Guide - NanoCoin Telegram Web App

This guide covers various deployment options for your NanoCoin game.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Bot token from [@BotFather](https://t.me/BotFather)
- [ ] Admin user IDs
- [ ] Domain name (for production) or ngrok for testing
- [ ] SSL certificate (for production) - Telegram requires HTTPS for Web Apps
- [ ] Database setup (SQLite for simple, PostgreSQL for production)

---

## 🏠 Option 1: Local Development

### Step 1: Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd NanoCoin_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
nano .env  # Edit with your values
```

### Step 2: Configure for Local Testing

```bash
# In .env, set:
BOT_TOKEN=your_token
ADMIN_IDS=your_telegram_id
DATABASE_URL=sqlite:///nanocoin.db
WEBAPP_URL=https://your-ngrok-url.ngrok.io/webapp
```

### Step 3: Run with ngrok

Terminal 1 - Start ngrok:
```bash
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok.io)
```

Terminal 2 - Run backend:
```bash
python -m backend.main
```

Terminal 3 - Run bot:
```bash
python -m bot.main
```

### Step 4: Test

Open Telegram, send `/start` to your bot, click "🎮 بازی کن!"

---

## 🐳 Option 2: Docker Deployment

### Quick Start

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Setup

1. **Edit docker-compose.yml** for PostgreSQL:
```yaml
services:
  nanocoin:
    environment:
      - DATABASE_URL=postgresql://nanocoin:password@postgres:5432/nanocoin
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: nanocoin
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: nanocoin
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

2. **Update .env**:
```bash
WEBAPP_URL=https://yourdomain.com/webapp
```

3. **Run**:
```bash
docker-compose up -d
```

---

## ☁️ Option 3: VPS Deployment (Ubuntu/Debian)

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx -y

# Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib -y
```

### Step 2: Setup Application

```bash
# Create user
sudo useradd -m -s /bin/bash nanocoin
sudo su - nanocoin

# Clone repository
git clone <your-repo-url> ~/nanocoin
cd ~/nanocoin

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env
```

### Step 3: Configure Systemd Services

Create `/etc/systemd/system/nanocoin-api.service`:
```ini
[Unit]
Description=NanoCoin FastAPI Backend
After=network.target

[Service]
Type=simple
User=nanocoin
WorkingDirectory=/home/nanocoin/nanocoin
Environment="PATH=/home/nanocoin/nanocoin/venv/bin"
ExecStart=/home/nanocoin/nanocoin/venv/bin/python -m backend.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/nanocoin-bot.service`:
```ini
[Unit]
Description=NanoCoin Telegram Bot
After=network.target

[Service]
Type=simple
User=nanocoin
WorkingDirectory=/home/nanocoin/nanocoin
Environment="PATH=/home/nanocoin/nanocoin/venv/bin"
ExecStart=/home/nanocoin/nanocoin/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nanocoin-api nanocoin-bot
sudo systemctl start nanocoin-api nanocoin-bot

# Check status
sudo systemctl status nanocoin-api
sudo systemctl status nanocoin-bot
```

### Step 4: Configure Nginx

Create `/etc/nginx/sites-available/nanocoin`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webapp {
        proxy_pass http://127.0.0.1:8000/webapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/nanocoin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: SSL with Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com
```

### Step 6: Update .env

```bash
WEBAPP_URL=https://yourdomain.com/webapp
```

Restart services:
```bash
sudo systemctl restart nanocoin-api nanocoin-bot
```

---

## 🌐 Option 4: Render.com Deployment

### Step 1: Prepare Repository

Create `render.yaml` in root:
```yaml
services:
  - type: web
    name: nanocoin-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m backend.main & python -m bot.main
    healthCheckPath: /health
    envVars:
      - key: BOT_TOKEN
        sync: false
      - key: ADMIN_IDS
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: WEBAPP_URL
        sync: false
      - key: API_HOST
        value: 0.0.0.0
      - key: API_PORT
        value: 8000
```

### Step 2: Deploy

1. Push code to GitHub
2. Go to [Render.com](https://render.com)
3. Connect repository
4. Add environment variables:
   - `BOT_TOKEN`: Your bot token
   - `ADMIN_IDS`: Your Telegram ID
   - `DATABASE_URL`: Use Render's PostgreSQL or SQLite
   - `WEBAPP_URL`: `https://your-app-name.onrender.com/webapp`

5. Deploy!

---

## 🚂 Option 5: Railway.app Deployment

### Step 1: Prepare

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python -m backend.main & python -m bot.main",
    "healthcheckPath": "/health"
  }
}
```

### Step 2: Deploy

1. Push to GitHub
2. Go to [Railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Add environment variables
5. Deploy

Set `WEBAPP_URL` to: `https://your-app.up.railway.app/webapp`

---

## 🔧 Post-Deployment Configuration

### 1. Set Bot Menu Button

After deployment, you can set a persistent menu button:

```python
# Run this once
from telegram import Bot, MenuButtonWebApp, WebAppInfo

bot = Bot(token="YOUR_BOT_TOKEN")
bot.set_chat_menu_button(
    menu_button=MenuButtonWebApp(
        text="🎮 Play Game",
        web_app=WebAppInfo(url="https://yourdomain.com/webapp")
    )
)
```

### 2. Database Migration

If using PostgreSQL, run migrations:
```bash
# The app auto-creates tables on startup via init_db()
# No manual migration needed
```

### 3. Monitoring

Add logging and monitoring:

```python
# backend/main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🔒 Production Security Checklist

- [ ] Change `SECRET_KEY` to a random string
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS (required by Telegram)
- [ ] Set proper CORS origins (not `*`)
- [ ] Add rate limiting
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Use environment variables for secrets
- [ ] Keep dependencies updated

---

## 📊 Monitoring & Maintenance

### View Logs

**Docker:**
```bash
docker-compose logs -f nanocoin
```

**Systemd:**
```bash
sudo journalctl -u nanocoin-api -f
sudo journalctl -u nanocoin-bot -f
```

### Database Backup

**SQLite:**
```bash
cp data/nanocoin.db data/nanocoin.db.backup
```

**PostgreSQL:**
```bash
pg_dump nanocoin > backup.sql
```

### Update Application

```bash
git pull origin main
sudo systemctl restart nanocoin-api nanocoin-bot
```

---

## 🐛 Troubleshooting

### Web App doesn't open

1. Check `WEBAPP_URL` is correct and uses HTTPS
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check bot logs for errors

### Authentication fails

1. Verify `BOT_TOKEN` is correct
2. Check Telegram WebApp SDK is loaded
3. Test initData validation manually

### Database errors

1. Check `DATABASE_URL` format
2. Ensure database exists
3. Verify permissions

### High latency

1. Use PostgreSQL instead of SQLite
2. Add database indexes
3. Enable caching
4. Use CDN for static files

---

## 📈 Scaling

### For high traffic:

1. **Use PostgreSQL** with connection pooling
2. **Add Redis** for caching and sessions
3. **Multiple workers** with Gunicorn:
   ```bash
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
4. **Load balancer** with multiple instances
5. **CDN** for webapp static files
6. **Database read replicas** for leaderboards

---

## 🎉 Success!

Your NanoCoin Web App is now deployed! Users can:

1. Open your bot in Telegram
2. Send `/start`
3. Click "🎮 بازی کن!"
4. Play the game in the Web App

For support, check the [REFACTORING_GUIDE.md](./REFACTORING_GUIDE.md)
