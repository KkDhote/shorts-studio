#!/usr/bin/env python3
"""
Interactive Instagram Account Setup Wizard for Agent k4.
Handles:
1. Direct Instagram Login (Username & Password) with live 2FA verification in the same session.
2. Browser Session ID (Instant, bypasses all 2FA & app checks).
3. Meta Graph API (Official Access Token & User ID).
"""

import os
import sys
import json
import getpass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "credentials" / "instagram_config.json"
SESSION_FILE = BASE_DIR / "credentials" / "instagram_session.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "login_method": "direct",
        "username": "kuldeepbhai_gamer",
        "password": "",
        "page_handle": "@kuldeepbhai_gamer",
        "auto_publish_enabled": True
    }

def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def test_sessionid_login(sessionid: str):
    from instagrapi import Client
    cl = Client()
    print(f"\n[setup_instagram] Authenticating via Instagram session ID...")
    try:
        cl.login_by_sessionid(sessionid.strip())
        cl.dump_settings(str(SESSION_FILE))
        user_info = cl.account_info()
        print(f"✅ Login SUCCESSFUL!")
        print(f"   Account: @{user_info.username} ({user_info.full_name})")
        print(f"   Followers: {user_info.follower_count} | Posts: {user_info.media_count}")
        print(f"   Saved permanent session to: {SESSION_FILE.name}")
        
        cfg = load_config()
        cfg["login_method"] = "direct"
        cfg["username"] = user_info.username
        cfg["page_handle"] = f"@{user_info.username}"
        cfg["sessionid"] = sessionid.strip()
        save_config(cfg)
        return True, cl
    except Exception as e:
        print(f"❌ Session ID login failed: {e}")
        return False, None

def test_direct_login(username, password):
    from instagrapi import Client
    from instagrapi.exceptions import TwoFactorRequired, ClientError
    cl = Client()
    cl.username = username
    cl.password = password
    print(f"\n[setup_instagram] Attempting login for @{username}...")
    try:
        try:
            cl.login(username, password)
        except TwoFactorRequired as exc:
            print("\n🔐 Two-Factor Authentication (2FA) is active on this account!")
            code = input("👉 Enter the 6-digit code received on your phone / app: ").strip()
            cl._login_with_bloks_two_factor(code, getattr(cl, "last_json", {}) or {}, exc)
        
        cl.dump_settings(str(SESSION_FILE))
        user_info = cl.account_info()
        print(f"\n✅ Login SUCCESSFUL!")
        print(f"   Account: @{user_info.username} ({user_info.full_name})")
        print(f"   Followers: {user_info.follower_count} | Posts: {user_info.media_count}")
        print(f"   Saved permanent session to: {SESSION_FILE.name}")
        
        cfg = load_config()
        cfg["login_method"] = "direct"
        cfg["username"] = user_info.username
        cfg["password"] = password
        cfg["page_handle"] = f"@{user_info.username}"
        save_config(cfg)
        return True, cl

    except Exception as e:
        print(f"\n❌ Login error: {e}")
        print("\n💡 TIP: If mobile CAA login is restricted, you can also login using your browser sessionid:")
        print("   1. Open instagram.com (where you are logged in)")
        print("   2. Inspect -> Application -> Cookies -> sessionid")
        print("   3. Run: python scripts/setup_instagram.py --sessionid <VALUE>")
        return False, None

def main():
    print("=" * 65)
    print(" 📸 AGENT k4: INSTAGRAM ACCOUNT SETUP WIZARD")
    print("=" * 65)
    print("Select your preferred setup method:")
    print(" 1. Direct Login (Username & Password with live 2FA prompt)")
    print(" 2. Browser Session ID (Instant, bypasses all 2FA & app checks)")
    print(" 3. View Current Configuration")
    print("=" * 65)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--view":
            cfg = load_config()
            print(f"\nCurrent Configuration ({CONFIG_FILE.name}):")
            print(f" - Username: {cfg.get('username') or 'Not set'}")
            print(f" - Session file exists: {SESSION_FILE.exists()}")
            return
        elif sys.argv[1] == "--sessionid" and len(sys.argv) > 2:
            test_sessionid_login(sys.argv[2])
            return

    cfg = load_config()
    default_user = cfg.get("username", "kuldeepbhai_gamer")
    default_pass = cfg.get("password", "LimeBeast@2004")

    choice = input("Enter choice (1/2/3) [default: 1]: ").strip() or "1"

    if choice == "1":
        print("\n--- Direct Instagram Login Setup ---")
        prompt_user = f"Enter Instagram Username [{default_user}]: "
        username = input(prompt_user).strip() or default_user

        if default_pass:
            use_saved = input("Use saved password from credentials? (Y/n): ").strip().lower()
            if use_saved != "n":
                password = default_pass
            else:
                password = getpass.getpass("Enter Instagram Password: ").strip()
        else:
            password = getpass.getpass("Enter Instagram Password: ").strip()

        test_direct_login(username, password)

    elif choice == "2":
        print("\n--- Browser Session ID Setup ---")
        print("1. In your browser (where you are logged into Instagram):")
        print("   Press F12 -> Application -> Cookies -> https://www.instagram.com")
        print("2. Copy the value of 'sessionid'")
        sid = input("Paste your sessionid here: ").strip()
        if sid:
            test_sessionid_login(sid)

    elif choice == "3":
        print(f"\nCurrent Configuration ({CONFIG_FILE.name}):")
        print(f" - Username: {cfg.get('username') or 'Not set'}")
        print(f" - Session file exists: {SESSION_FILE.exists()}")

if __name__ == "__main__":
    main()
