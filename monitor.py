import os
import requests
import json
from datetime import datetime, timedelta
import time

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ISI_TOKEN_KAMU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ISI_CHAT_ID_KAMU")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "ISI_RAPIDAPI_KEY_KAMU")

MIN_VIEWS = 50000
MAX_HOURS = 10

KEYWORDS = [
    "TKI Taiwan",
    "PMI Taiwan",
    "Taiwan viral",
    "viral Taiwan Indonesia",
    "TKI 2025",
    "kerja Taiwan",
    "buruh migran Taiwan"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Telegram terkirim")
        else:
            print(f"❌ Gagal kirim Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

def search_tiktok_videos(keyword):
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"}
    params = {"keywords": keyword, "region": "ID", "count": "20", "cursor": "0", "publish_time": "1", "sort_type": "1"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("videos", [])
        else:
            print(f"❌ Error API untuk '{keyword}': {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception untuk '{keyword}': {e}")
        return []

def is_viral(video):
    try:
        play_count = video.get("play_count", 0)
        create_time = video.get("create_time", 0)
        if not create_time:
            return False, 0, 0
        video_time = datetime.fromtimestamp(create_time)
        now = datetime.now()
        age_hours = (now - video_time).total_seconds() / 3600
        if play_count >= MIN_VIEWS and age_hours <= MAX_HOURS:
            return True, play_count, age_hours
        return False, play_count, age_hours
    except Exception as e:
        return False, 0, 0

def format_views(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    return str(num)

def run_monitor():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"🔍 Mulai monitoring: {now}")
    send_telegram(f"🤖 <b>TKI Monitor aktif</b>\n📅 Cek dimulai: {now}\​​​​​​​​​​​​​​​​

