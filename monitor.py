import os
import requests
from datetime import datetime, timedelta
import time
from collections import defaultdict

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

VIRAL_MIN_VIEWS = 100000
VIRAL_MAX_HOURS = 12
TAG_MIN_VIEWS = 100000
TAG_MIN_VIDEOS = 3
TAG_MAX_HOURS = 24

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

VIRAL_KEYWORDS = [
    "viral indonesia",
    "trending indonesia",
    "viral tiktok indonesia",
    "fyp indonesia",
    "viral hari ini"
]

TREND_KEYWORDS = [
    "viral indonesia 2025",
    "trending indonesia",
    "fyp indonesia viral",
    "viral tiktok indo",
    "lagu viral indonesia"
]

SKIP_HASHTAGS = {
    "fyp", "foryou", "foryoupage", "viral", "trending",
    "tiktok", "fypシ", "fypシ゚viral", "fy", "indonesia",
    "fyppppp", "myvideo", "xybca"
}

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

def extract_hashtags(text):
    words = text.split()
    return [w.lower().strip("#.,!?") for w in words if w.startswith("#") and len(w) > 2]

def run_viral_monitor():
    print("\n🇮🇩 Monitor Video Viral Indonesia...")
    viral_videos = []
    checked_ids = set()
    for keyword in VIRAL_KEYWORDS:
        print(f"  🔎 '{keyword}'")
        for video in search_videos(keyword):
            video_id = video.get("video_id", "")
            if video_id in checked_ids:
                continue
            checked_ids.add(video_id)
            play_count = video.get("play_count", 0)
            age_hours = get_age_hours(video.get("create_time", 0))
            if play_count >= VIRAL_MIN_VIEWS and age_hours <= VIRAL_MAX_HOURS:
                username = video.get("author", {}).get("unique_id", "unknown")
                viral_videos.append({
                    "username": username,
                    "views": play_count,
                    "age_hours": round(age_hours, 1),
                    "desc": video.get("title", "")[:100],
                    "url": f"https://www.tiktok.com/@{username}/video/{video_id}",
                    "keyword": keyword
                })
        time.sleep(2)
    return viral_videos

def run_hashtag_monitor():
    print("\n#️⃣ Monitor Hashtag Trending...")
    all_videos = []
    checked_ids = set()
    for keyword in TREND_KEYWORDS:
        print(f"  🔎 '{keyword}'")
        for v in search_videos(keyword):
            vid_id = v.get("video_id", "")
            if vid_id and vid_id not in checked_ids:
                checked_ids.add(vid_id)
                all_videos.append(v)
        time.sleep(2)

    hashtag_groups = defaultdict(lambda: {"videos": [], "total_views": 0})
    for video in all_videos:
        play_count = video.get("play_count", 0)
        age_hours = get_age_hours(video.get("create_time", 0))
        if play_count < TAG_MIN_VIEWS or age_hours > TAG_MAX_HOURS:
            continue
        username = video.get("author", {}).get("unique_id", "unknown")
        video_id = video.get("video_id", "")
        video_data = {
            "username": username,
            "views": play_count,
            "url": f"https://www.tiktok.com/@{username}/video/{video_id}"
        }
        for tag in extract_hashtags(video.get("title", "")):
            if tag in SKIP_HASHTAGS or len(tag) < 3:
                continue
            hashtag_groups[tag]["videos"].append(video_data)
            hashtag_groups[tag]["total_views"] += play_count

    return dict(sorted(
        {k: v for k, v in hashtag_groups.items() if len(v["videos"]) >= TAG_MIN_VIDEOS}.items(),
        key=lambda x: x[1]["total_views"], reverse=True
    ))

def run_monitor():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n🚀 Monitoring: {now}")
    send_telegram(f"🤖 <b>Indo Viral Monitor aktif</b>\n📅 {now}\n🔍 Cek video viral + hashtag trending...")

    # PART 1: VIDEO VIRAL INDONESIA
    viral_videos = run_viral_monitor()
    if viral_videos:
        send_telegram(f"🇮🇩 <b>VIDEO VIRAL INDONESIA 1M+!</b>\n📊 {len(viral_videos)} video\n⏰ {now}")
        for i, v in enumerate(viral_videos[:5]):
            msg = f"🎵 <b>Video #{i+1}</b>\n"
            msg += f"👤 @{v['username']}\n"
            msg += f"📺 Views: <b>{format_views(v['views'])}</b>\n"
            msg += f"⏱ Umur: {v['age_hours']} jam\n"
            msg += f"🔍 {v['keyword']}\n"
            msg += f"📝 {v['desc']}\n"
            msg += f"🔗 {v['url']}"
            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(f"🇮🇩 <b>Video Viral Indonesia</b>\n✅ Tidak ada video 1M+ views dalam 12 jam")

    time.sleep(3)

    # PART 2: HASHTAG TRENDING
    trending = run_hashtag_monitor()
    if trending:
        send_telegram(f"🔥 <b>HASHTAG TRENDING INDONESIA!</b>\n📊 {len(trending)} hashtag viral\n⏰ {now}")
        for tag, data in list(trending.items())[:5]:
            videos = sorted(data["videos"], key=lambda x: x["views"], reverse=True)
            msg = f"#️⃣ <b>#{tag}</b>\n"
            msg += f"📹 {len(videos)} video\n"
            msg += f"👁 Total: <b>{format_views(data['total_views'])}</b>\n\n"
            msg += "<b>Top videos:</b>\n"
            for i, v in enumerate(videos[:5]):
                msg += f"{i+1}. @{v['username']} — {format_views(v['views'])} views\n{v['url']}\n"
            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(f"#️⃣ <b>Hashtag Trending</b>\n✅ Belum ada hashtag dengan {TAG_MIN_VIDEOS}+ video {format_views(TAG_MIN_VIEWS)}+ views")

    print(f"✅ Selesai.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 Indo Viral Monitor dimulai!")
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
