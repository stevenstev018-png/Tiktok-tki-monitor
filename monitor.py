import os
import requests
from datetime import datetime, timedelta
import time
from collections import defaultdict

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

MIN_VIEWS = 100000
MIN_VIDEOS_PER_HASHTAG = 3
MAX_HOURS = 24

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

KEYWORDS = [
    "viral indonesia 2025",
    "trending indonesia",
    "fyp indonesia viral",
    "viral tiktok indo",
    "lagu viral indonesia"
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
    params = {"keywords": keyword, "region": "ID", "count": "30", "cursor": "0", "publish_time": "1", "sort_type": "1"}
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {}).get("videos", [])
        return []
    except:
        return []

def extract_hashtags(text):
    """Ambil semua hashtag dari caption video"""
    words = text.split()
    return [w.lower().strip("#.,!") for w in words if w.startswith("#") and len(w) > 1]

def format_views(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    return str(num)

def is_recent(create_time):
    try:
        age_hours = (datetime.now() - datetime.fromtimestamp(create_time)).total_seconds() / 3600
        return age_hours <= MAX_HOURS
    except:
        return False

def run_monitor():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"🔍 Mulai monitoring: {now}")
    send_telegram(f"🤖 <b>TKI Trend Monitor aktif</b>\n📅 {now}\n#️⃣ Mencari hashtag trending Indonesia...")

    # Step 1: Kumpulkan semua video
    all_videos = []
    checked_ids = set()

    for keyword in KEYWORDS:
        print(f"🔎 Search: '{keyword}'")
        videos = search_videos(keyword)
        for v in videos:
            vid_id = v.get("video_id", "")
            if vid_id and vid_id not in checked_ids:
                checked_ids.add(vid_id)
                all_videos.append(v)
        time.sleep(2)

    print(f"📊 Total video: {len(all_videos)}")

    # Step 2: Kelompokkan berdasarkan hashtag
    hashtag_groups = defaultdict(lambda: {"videos": [], "total_views": 0})
    
    # Hashtag yang terlalu umum, skip
    skip_hashtags = {"fyp", "foryou", "foryoupage", "viral", "trending", "tiktok", "fypシ", "fypシ゚viral", "fy"}

    for video in all_videos:
        play_count = video.get("play_count", 0)
        create_time = video.get("create_time", 0)

        if play_count < MIN_VIEWS or not is_recent(create_time):
            continue

        title = video.get("title", "")
        hashtags = extract_hashtags(title)
        username = video.get("author", {}).get("unique_id", "unknown")
        video_id = video.get("video_id", "")
        video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"

        video_data = {
            "username": username,
            "views": play_count,
            "url": video_url,
            "title": title[:80]
        }

        for tag in hashtags:
            if tag in skip_hashtags or len(tag) < 3:
                continue
            hashtag_groups[tag]["videos"].append(video_data)
            hashtag_groups[tag]["total_views"] += play_count

    # Step 3: Filter hashtag yang muncul di 3+ video
    trending_hashtags = {
        k: v for k, v in hashtag_groups.items()
        if len(v["videos"]) >= MIN_VIDEOS_PER_HASHTAG
    }

    # Sort by total views
    trending_hashtags = dict(
        sorted(trending_hashtags.items(), key=lambda x: x[1]["total_views"], reverse=True)
    )

    print(f"🔥 {len(trending_hashtags)} hashtag trending ditemukan!")

    # Step 4: Kirim alert
    if trending_hashtags:
        send_telegram(f"🔥 <b>HASHTAG TRENDING INDONESIA!</b>\n📊 {len(trending_hashtags)} hashtag viral\n⏰ {now}")

        for tag, data in list(trending_hashtags.items())[:5]:
            videos = sorted(data["videos"], key=lambda x: x["views"], reverse=True)
            total_views = data["total_views"]

            msg = f"#️⃣ <b>#{tag}</b>\n"
            msg += f"📹 {len(videos)} video pakai hashtag ini\n"
            msg += f"👁 Total views: <b>{format_views(total_views)}</b>\n\n"
            msg += "<b>Top videos:</b>\n"
            for i, v in enumerate(videos[:5]):
                msg += f"{i+1}. @{v['username']} — {format_views(v['views'])} views\n{v['url']}\n"
            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(
            f"✅ <b>Monitoring selesai</b>\n"
            f"⏰ {now}\n"
            f"📊 Belum ada hashtag dengan {MIN_VIDEOS_PER_HASHTAG}+ video {format_views(MIN_VIEWS)}+ views\n"
            f"🔄 Cek berikutnya jam 7 pagi/malam"
        )

    print(f"✅ Selesai. {len(trending_hashtags)} hashtag trending.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 TKI Trend Monitor dimulai!")
    mode = os.environ.get("RUN_MODE", "scheduled")
    if mode == "test":
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
                print(f"💤 [{now_wib.strftime('%d/%m %H:%M')} WIB] Menunggu...")
            time.sleep(300)
