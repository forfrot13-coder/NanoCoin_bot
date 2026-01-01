#!/usr/bin/env python3
"""
Quick setup verification script for NanoCoin Web App
"""

import sys
import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Run: cp .env.example .env")
        return False
    
    # Check for required variables
    with open(env_path) as f:
        content = f.read()
        required = ['BOT_TOKEN', 'ADMIN_IDS', 'WEBAPP_URL']
        missing = []
        for var in required:
            if var not in content or f'{var}=your_' in content:
                missing.append(var)
        
        if missing:
            print(f"❌ Missing or not configured: {', '.join(missing)}")
            print("   Edit .env file with your actual values")
            return False
    
    print("✅ .env file configured")
    return True

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import telegram
        import fastapi
        import sqlalchemy
        print("✅ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def check_directory_structure():
    """Check if all required directories exist"""
    required_dirs = [
        'bot',
        'backend',
        'backend/routers',
        'backend/services',
        'backend/schemas',
        'webapp',
        'webapp/js',
        'webapp/css',
        'database'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            all_exist = False
    
    if all_exist:
        print("✅ All directories present")
    return all_exist

def check_database():
    """Check database connection"""
    try:
        from database.connection import init_db, get_session
        init_db()
        session = get_session()
        session.close()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_webapp_files():
    """Check if webapp files exist"""
    required_files = [
        'webapp/index.html',
        'webapp/css/styles.css',
        'webapp/js/app.js',
        'webapp/js/api.js',
        'webapp/js/game.js',
        'webapp/js/shop.js',
        'webapp/js/utils.js'
    ]
    
    all_exist = True
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing file: {file_path}")
            all_exist = False
    
    if all_exist:
        print("✅ All webapp files present")
    return all_exist

def main():
    print("🔍 NanoCoin Setup Verification\n")
    print("=" * 50)
    
    checks = [
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Database", check_database),
        ("WebApp Files", check_webapp_files)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking: {name}")
        results.append(check_func())
    
    print("\n" + "=" * 50)
    
    if all(results):
        print("\n✅ All checks passed! You're ready to run the app.")
        print("\nNext steps:")
        print("1. Terminal 1: python -m backend.main")
        print("2. Terminal 2: python -m bot.main")
        print("3. Open your bot in Telegram and send /start")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
