import os
import requests
from datetime import datetime, timedelta
import time
from collections import defaultdict

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

MIN_VIEWS = 100000
MIN_VIDEOS_PER_SOUND = 3
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
        print(f"❌ Search error {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def get_music_videos(music_id):
    url = "https://tiktok-scraper7.p.rapidapi.com/music/posts"
    params = {"music_id": music_id, "count": "30", "cursor": "0"}
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", {}).get("videos", [])
        return []
    except:
        return []

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
    send_telegram(f"🤖 <b>TKI Sound Monitor aktif</b>\n📅 {now}\n🎵 Mencari sound viral Indonesia...")

    # Step 1: Kumpulkan video dari search
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

    print(f"📊 Total video terkumpul: {len(all_videos)}")

    # Step 2: Kelompokkan berdasarkan music/sound
    sound_groups = defaultdict(lambda: {"music_title": "", "music_author": "", "music_id": "", "videos": []})

    for video in all_videos:
        music = video.get("music_info", {})
        if not music:
            continue

        music_id = str(music.get("id", ""))
        if not music_id:
            continue

        play_count = video.get("play_count", 0)
        create_time = video.get("create_time", 0)

        if play_count < MIN_VIEWS or not is_recent(create_time):
            continue

        username = video.get("author", {}).get("unique_id", "unknown")
        video_id = video.get("video_id", "")

        sound_groups[music_id]["music_title"] = music.get("title", "Unknown Sound")
        sound_groups[music_id]["music_author"] = music.get("author", "Unknown")
        sound_groups[music_id]["music_id"] = music_id
        sound_groups[music_id]["videos"].append({
            "username": username,
            "views": play_count,
            "url": f"https://www.tiktok.com/@{username}/video/{video_id}"
        })

    # Step 3: Untuk sound yang muncul, cek lebih banyak videonya
    promising_sounds = {k: v for k, v in sound_groups.items() if len(v["videos"]) >= 1}
    print(f"🎵 {len(promising_sounds)} sound ditemukan, cek lebih dalam...")

    trending_sounds = {}

    for music_id, data in list(promising_sounds.items())[:10]:
        print(f"   Cek sound: {data['music_title']}")
        more_videos = get_music_videos(music_id)

        viral_vids = list(data["videos"])  # mulai dari yang sudah ada
        existing_ids = {v["url"] for v in viral_vids}

        for v in more_videos:
            play_count = v.get("play_count", 0)
            create_time = v.get("create_time", 0)
            username = v.get("author", {}).get("unique_id", "unknown")
            video_id = v.get("video_id", "")
            url = f"https://www.tiktok.com/@{username}/video/{video_id}"

            if play_count >= MIN_VIEWS and is_recent(create_time) and url not in existing_ids:
                viral_vids.append({"username": username, "views": play_count, "url": url})
                existing_ids.add(url)

        if len(viral_vids) >= MIN_VIDEOS_PER_SOUND:
            trending_sounds[music_id] = {
                "music_title": data["music_title"],
                "music_author": data["music_author"],
                "videos": sorted(viral_vids, key=lambda x: x["views"], reverse=True)
            }

        time.sleep(1)

    # Step 4: Kirim alert
    print(f"🔥 {len(trending_sounds)} sound trending ditemukan!")

    if trending_sounds:
        send_telegram(f"🔥 <b>SOUND VIRAL INDONESIA!</b>\n📊 {len(trending_sounds)} sound trending\n⏰ {now}")

        for sound_id, data in list(trending_sounds.items())[:3]:
            total_views = sum(v["views"] for v in data["videos"])
            msg = f"🎵 <b>{data['music_title']}</b>\n"
            msg += f"👤 By: {data['music_author']}\n"
            msg += f"📹 {len(data['videos'])} video pakai sound ini\n"
            msg += f"👁 Total views: <b>{format_views(total_views)}</b>\n\n"
            msg += "<b>Top videos:</b>\n"
            for i, v in enumerate(data["videos"][:5]):
                msg += f"{i+1}. @{v['username']} — {format_views(v['views'])} views\n{v['url']}\n"
            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(f"✅ <b>Monitoring selesai</b>\n⏰ {now}\n📊 Belum ada sound dengan {MIN_VIDEOS_PER_SOUND}+ video {format_views(MIN_VIEWS)}+ views\n🔄 Cek berikutnya jam 7 pagi/malam")

    print(f"✅ Selesai. {len(trending_sounds)} sound viral.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 TKI Sound Monitor dimulai!")
    mode = os.environ.get("RUN_MODE", "scheduled")
    if mode == "test":
        run_monitor()
    else:
        print("⏳ Mode scheduled aktif...")
        last_run_date = None
        last_run_hour = None
        while True:
            now_
