import os
import requests
from datetime import datetime, timedelta
import time

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

MIN_VIEWS = 30000
MAX_HOURS = 8

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

KEYWORDS = [
    "TKI Taiwan",
    "PMI Taiwan",
    "Taiwan viral",
    "viral Taiwan Indonesia",
    "TKI 2025",
    "kerja Taiwan",
    "buruh migran Taiwan",
    "Indonesia Taiwan"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram terkirim")
        else:
            print(f"❌ Gagal: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def search_videos(keyword):
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"
    params = {
        "keywords": keyword,
        "region": "ID",
        "count": "30",
        "cursor": "0",
        "publish_time": "1",
        "sort_type": "1"
    }
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {}).get("videos", [])
        return []
    except:
        return []

def get_age_hours(create_time):
    try:
        return (datetime.now() - datetime.fromtimestamp(create_time)).total_seconds() / 3600
    except:
        return 999

def format_views(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    return str(num)

def run_monitor():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n🚀 Monitoring: {now}")
    send_telegram(f"🤖 <b>TKI Taiwan Monitor aktif</b>\n📅 {now}\n🔍 Mencari video viral TKI Taiwan...")

    viral_videos = []
    checked_ids = set()

    for keyword in KEYWORDS:
        print(f"  🔎 '{keyword}'")
        for video in search_videos(keyword):
            video_id = video.get("video_id", "")
            if video_id in checked_ids:
                continue
            checked_ids.add(video_id)

            play_count = video.get("play_count", 0)
            age_hours = get_age_hours(video.get("create_time", 0))

            if play_count >= MIN_VIEWS and age_hours <= MAX_HOURS:
                username = video.get("author", {}).get("unique_id", "unknown")
                desc = video.get("title", "")[:100]
                viral_videos.append({
                    "username": username,
                    "views": play_count,
                    "age_hours": round(age_hours, 1),
                    "desc": desc,
                    "url": f"https://www.tiktok.com/@{username}/video/{video_id}",
                    "keyword": keyword
                })
                print(f"  🔥 @{username} — {format_views(play_count)} views")
        time.sleep(2)

    if viral_videos:
        viral_videos = sorted(viral_videos, key=lambda x: x["views"], reverse=True)
        send_telegram(
            f"🔥 <b>VIDEO VIRAL TKI TAIWAN!</b>\n"
            f"📊 {len(viral_videos)} video ditemukan\n"
            f"⏰ {now}"
        )
        for i, v in enumerate(viral_videos[:5]):
            msg = f"🎥 <b>Video #{i+1}</b>\n"
            msg += f"👤 @{v['username']}\n"
            msg += f"📺 Views: <b>{format_views(v['views'])}</b>\n"
            msg += f"⏱ Umur: {v['age_hours']} jam\n"
            msg += f"🔍 Keyword: {v['keyword']}\n"
            msg += f"📝 {v['desc']}\n"
            msg += f"🔗 {v['url']}"
            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(
            f"✅ <b>Monitoring selesai</b>\n"
            f"⏰ {now}\n"
            f"📊 Tidak ada video viral baru\n"
            f"(threshold: {format_views(MIN_VIEWS)} views dalam {MAX_HOURS} jam)\n"
            f"🔄 Cek berikutnya jam 7 pagi/malam"
        )

    print(f"✅ Selesai. {len(viral_videos)} video viral.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 TKI Taiwan Monitor dimulai!")
    mode = os.environ.get("RUN_MODE", "scheduled")
    if mode == "test":
        run_monitor()
    else:
        print("⏳ Scheduled aktif...")
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
                print(f"💤 [{now_wib.strftime('%d/%m %H:%M')} WIB] Menunggu...")
            time.sleep(300)
