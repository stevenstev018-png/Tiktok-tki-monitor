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

def get_fyp_videos():
    """Ambil video trending FYP Indonesia"""
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/list"
    params = {"region": "ID", "count": "50"}
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("videos", [])
        print(f"❌ FYP API error: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ FYP exception: {e}")
        return []

def get_music_videos(music_id):
    """Ambil semua video yang pakai sound tertentu"""
    url = "https://tiktok-scraper7.p.rapidapi.com/music/posts"
    params = {"music_id": music_id, "count": "20", "cursor": "0"}
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("videos", [])
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
    """Cek apakah video dibuat dalam 24 jam terakhir"""
    try:
        age_hours = (datetime.now() - datetime.fromtimestamp(create_time)).total_seconds() / 3600
        return age_hours <= MAX_HOURS
    except:
        return False

def run_monitor():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"🔍 Mulai monitoring sound viral: {now}")
    send_telegram(f"🤖 <b>TKI Sound Monitor aktif</b>\n📅 {now}\n🎵 Mencari sound viral Indonesia...")

    # Step 1: Ambil video FYP Indonesia
    print("📱 Mengambil video FYP Indonesia...")
    fyp_videos = get_fyp_videos()
    print(f"   Dapat {len(fyp_videos)} video dari FYP")

    if not fyp_videos:
        send_telegram(f"⚠️ Tidak bisa ambil data FYP. Coba lagi nanti.")
        return

    # Step 2: Kelompokkan berdasarkan sound/music
    sound_groups = defaultdict(lambda: {"music_title": "", "music_author": "", "music_id": "", "videos": []})

    for video in fyp_videos:
        music = video.get("music_info", {})
        if not music:
            continue

        music_id = str(music.get("id", ""))
        music_title = music.get("title", "Unknown Sound")
        music_author = music.get("author", "Unknown")
        play_count = video.get("play_count", 0)
        create_time = video.get("create_time", 0)

        if not music_id or play_count < MIN_VIEWS:
            continue

        if not is_recent(create_time):
            continue

        author = video.get("author", {})
        username = author.get("unique_id", "unknown")
        video_id = video.get("video_id", "")
        video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"

        sound_groups[music_id]["music_title"] = music_title
        sound_groups[music_id]["music_author"] = music_author
        sound_groups[music_id]["music_id"] = music_id
        sound_groups[music_id]["videos"].append({
            "username": username,
            "views": play_count,
            "url": video_url,
            "video_id": video_id
        })

    # Step 3: Filter sound yang dipakai 3+ video
    trending_sounds = {k: v for k, v in sound_groups.items() if len(v["videos"]) >= MIN_VIDEOS_PER_SOUND}

    print(f"🎵 Ditemukan {len(trending_sounds)} sound trending (3+ video 100k+ views)")

    if not trending_sounds:
        # Coba cek lebih dalam via music API
        print("🔍 FYP kurang, cek via search...")
        
        # Kumpulkan semua music_id dari FYP
        all_music_ids = defaultdict(lambda: {"music_title": "", "music_author": "", "videos": []})
        for video in fyp_videos:
            music = video.get("music_info", {})
            if not music:
                continue
            music_id = str(music.get("id", ""))
            if not music_id:
                continue
            all_music_ids[music_id]["music_title"] = music.get("title", "Unknown")
            all_music_ids[music_id]["music_author"] = music.get("author", "Unknown")

        # Cek top 5 music_id yang paling sering muncul
        top_music = sorted(all_music_ids.items(), key=lambda x: len(x[1]["videos"]), reverse=True)[:5]

        for music_id, info in top_music:
            print(f"   Cek sound: {info['music_title']}")
            music_videos = get_music_videos(music_id)
            
            viral_vids = []
            for v in music_videos:
                play_count = v.get("play_count", 0)
                create_time = v.get("create_time", 0)
                if play_count >= MIN_VIEWS and is_recent(create_time):
                    username = v.get("author", {}).get("unique_id", "unknown")
                    video_id = v.get("video_id", "")
                    viral_vids.append({
                        "username": username,
                        "views": play_count,
                        "url": f"https://www.tiktok.com/@{username}/video/{video_id}"
                    })
            
            if len(viral_vids) >= MIN_VIDEOS_PER_SOUND:
                trending_sounds[music_id] = {
                    "music_title": info["music_title"],
                    "music_author": info["music_author"],
                    "videos": viral_vids
                }
            time.sleep(1)

    # Step 4: Kirim alert
    if trending_sounds:
        header = f"🔥 <b>SOUND VIRAL INDONESIA DITEMUKAN!</b>\n"
        header += f"📊 {len(trending_sounds)} sound trending\n"
        header += f"⏰ {now}\n"
        send_telegram(header)

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
        send_telegram(f"✅ <b>Monitoring selesai</b>\n⏰ {now}\n📊 Belum ada sound dengan 3+ video 100k+ views\n🔄 Cek berikutnya jam 7 pagi/malam")

    print(f"✅ Selesai. {len(trending_sounds)} sound viral ditemukan.")

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
            now_wib = datetime.utcnow() + timedelta(hours=7)
            if should_run():
                if last_run_date != now_wib.date() or last_run_hour != now_wib.hour:
                    run_monitor()
                    last_run_date = now_wib.date()
                    last_run_hour = now_wib.hour
            else:
                print(f"💤 [{now_wib.strftime('%d/%m %H:%M')} WIB] Menunggu...")
            time.sleep(300)
