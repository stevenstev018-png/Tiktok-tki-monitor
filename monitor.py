import os
import requests
from datetime import datetime, timedelta
import time
from collections import defaultdict

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

MIN_VIEWS = 100000
MAX_HOURS = 10
MIN_VIDEOS_PER_SOUND = 3

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

KEYWORDS = [
    "lagu viral tiktok 2025",
    "sound viral tiktok indonesia",
    "lagu trending tiktok indo",
    "musik viral indonesia tiktok",
    "tiktok sound viral indo"
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
    send_telegram(f"🤖 <b>Sound Viral Monitor aktif</b>\n📅 {now}\n🎵 Mencari sound/lagu viral Indonesia...")

    # Kumpulkan semua video
    all_videos = []
    checked_ids = set()

    for keyword in KEYWORDS:
        print(f"  🔎 '{keyword}'")
        for video in search_videos(keyword):
            video_id = video.get("video_id", "")
            if video_id in checked_ids:
                continue
            checked_ids.add(video_id)
            all_videos.append(video)
        time.sleep(2)

    print(f"  📊 Total video: {len(all_videos)}")

    # Kelompokkan berdasarkan sound/musik
    sound_groups = defaultdict(lambda: {
        "title": "",
        "author": "",
        "videos": []
    })

    for video in all_videos:
        play_count = video.get("play_count", 0)
        age_hours = get_age_hours(video.get("create_time", 0))

        if play_count < MIN_VIEWS or age_hours > MAX_HOURS:
            continue

        # Ambil info musik
        music = video.get("music_info", {})
        if not music:
            # Coba field lain
            music = video.get("music", {})
        
        music_id = str(music.get("id", "") or music.get("music_id", ""))
        music_title = music.get("title", "") or music.get("name", "")
        music_author = music.get("author", "") or music.get("artist", "")

        if not music_id or not music_title:
            continue

        username = video.get("author", {}).get("unique_id", "unknown")
        video_id = video.get("video_id", "")

        sound_groups[music_id]["title"] = music_title
        sound_groups[music_id]["author"] = music_author
        sound_groups[music_id]["videos"].append({
            "username": username,
            "views": play_count,
            "age_hours": round(age_hours, 1),
            "url": f"https://www.tiktok.com/@{username}/video/{video_id}"
        })

    # Filter sound yang muncul di 3+ video
    trending_sounds = {
        k: v for k, v in sound_groups.items()
        if len(v["videos"]) >= MIN_VIDEOS_PER_SOUND
    }

    # Sort by jumlah video terbanyak
    trending_sounds = dict(sorted(
        trending_sounds.items(),
        key=lambda x: len(x[1]["videos"]),
        reverse=True
    ))

    print(f"  🎵 {len(trending_sounds)} sound viral ditemukan!")

    if trending_sounds:
        send_telegram(
            f"🔥 <b>SOUND VIRAL INDONESIA!</b>\n"
            f"🎵 {len(trending_sounds)} lagu trending hari ini\n"
            f"⏰ {now}"
        )

        for sound_id, data in list(trending_sounds.items())[:5]:
            videos = sorted(data["videos"], key=lambda x: x["views"], reverse=True)
            total_views = sum(v["views"] for v in videos)

            msg = f"🎵 <b>{data['title']}</b>\n"
            msg += f"👤 Artist: {data['author']}\n"
            msg += f"📹 Dipakai {len(videos)} video viral\n"
            msg += f"👁 Total views: <b>{format_views(total_views)}</b>\n\n"
            msg += "<b>Contoh video yang pakai sound ini:</b>\n"

            for i, v in enumerate(videos[:5]):
                msg += f"{i+1}. @{v['username']} — {format_views(v['views'])} views ({v['age_hours']} jam)\n"
                msg += f"🔗 {v['url']}\n"

            send_telegram(msg)
            time.sleep(1)
    else:
        send_telegram(
            f"✅ <b>Monitoring selesai</b>\n"
            f"⏰ {now}\n"
            f"📊 Belum ada sound dengan {MIN_VIDEOS_PER_SOUND}+ video {format_views(MIN_VIEWS)}+ views dalam {MAX_HOURS} jam\n"
            f"🔄 Cek berikutnya jam 7 pagi/malam"
        )

    print(f"✅ Selesai. {len(trending_sounds)} sound viral.")

def should_run():
    now_wib = datetime.utcnow() + timedelta(hours=7)
    return (now_wib.hour == 7 or now_wib.hour == 19) and now_wib.minute < 5

if __name__ == "__main__":
    print("🚀 Sound Viral Monitor dimulai!")
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
