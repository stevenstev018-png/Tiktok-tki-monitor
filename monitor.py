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
    send_telegram(f"🤖 <b>TKI Monitor aktif</b>\n📅 Cek dimulai: {now}\n🔍 Mencari konten viral...")
    viral_videos = []
    checked_ids = set()
    for keyword in KEYWORDS:
        print(f"🔎 Mencari: '{keyword}'")
        videos = search_tiktok_videos(keyword)
        for video in videos:
            video_id = video.get("video_id", "")
            if video_id in checked_ids:
                continue
            checked_ids.add(video_id)
            is_vir, play_count, age_hours = is_viral(video)
            if is_vir:
                author = video.get("author", {})
                username = author.get("unique_id", "unknown")
                desc = video.get("title", "")[:100]
                video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                viral_videos.append({"id": video_id, "username": username, "desc": desc, "views": play_count, "age_hours": round(age_hours, 1), "url": video_url, "keyword": keyword})
                print(f"🔥 VIRAL! @{username} - {format_views(play_count)} views")
        time.sleep(2)
    if viral_videos:
        header = f"🔥 <b>KONTEN VIRAL TKI TAIWAN!</b>\n📊 {len(viral_videos)} video viral\n⏰ {now}\n\n"
        send_telegram(header)
        for i, v in enumerate(viral_videos[:5]):
            msg = f"🎵 <b>Video #{i+1}</b>\n👤 @{v['username']}\n📺 Views: <b>{format_views(v['views'])}</b>\n⏱ Umur: {v['age_hours']} jam\n🔍 Keyword: {v['keyword']}\n📝 {v['desc']}\n🔗 {v['url']}"
            send_telegram(msg)
            time.sleep(1)
    else:
        msg = f"✅ <b>Monitoring selesai</b>\n⏰ {now}\n📊 Tidak ada konten viral baru\n🔄 Cek berikutnya jam 7 pagi/malam"
        send_telegram(msg)
    print(f"✅ Selesai. {len(viral_videos)} video viral ditemukan.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 TKI Taiwan TikTok Monitor dimulai!")
    mode = os.environ.get("RUN_MODE", "scheduled")
    if mode == "test":
        print("🧪 MODE TEST")
        run_monitor()
    else:
        print("⏳ Mode scheduled aktif...")
        last_run_date = None
        last_run_hour = None
        while True:
            now_wib = datetime.utcnow() + timedelta(hours=7)
            if should_run():
                if last_run_date != now_wib.date() or last_run_hour != now_wib.hour:
                    run_monitor()
                    last_run_date = now_wib.date()
                    last_run_hour = now_wib.hour
            else:
                print(f"💤 [{now_wib.strftime('%d/%m %H:%M')} WIB] Menunggu jadwal...")
            time.sleep(300)
