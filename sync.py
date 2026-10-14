import os
import requests
import json
import uuid
import time

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-CMX1EDFBSM"
GA4_API_SECRET = "9AGO30IhQgyEnyioiZi9aA"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

COURSES_MAP = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

session = requests.Session()
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_to_ga4(event_name, item_name, count, target_url):
    for i in range(count):
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now_ts = int(time.time() * 1000000)
        
        payload = {
            "client_id": user_id,
            "timestamp_micros": now_ts,
            "events": [{
                "name": event_name,
                "params": {
                    "course_name": item_name,
                    "item_name": item_name,
                    "destination_url": target_url,
                    "session_id": str(int(time.time())),
                    "engagement_time_msec": 1000
                }
            }]
        }
        session.post(ga4_url, json=payload, timeout=5)
    print(f"-> [{event_name}] '{item_name}': успешно отправлено {count} кликов")

try:
    print("Получаем ссылки из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit(1)

    links = res.json()
    print(f"Получено ссылок: {len(links)}")

    for item in links:
        raw_key = item.get("key", "").strip()
        target_url = item.get("url", "").strip()
        clicks = max(item.get("clicks", 0), 1)

        # 1. ШЕСТЬ КУРСОВ -> в общую папку astanahub_courses
        if raw_key in COURSES_MAP:
            event_name = "astanahub_courses"
            item_name = COURSES_MAP[raw_key]

        # 2. КАТАЛОГ PDF: ЭКРАНЫ
        elif "iseh4b" in raw_key:
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"

        # 3. КАТАЛОГ PDF: ДЛЯ ПРЕЗЕНТАЦИЙ
        elif "vjfi9b" in raw_key:
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"

        # 4. ДЕЦЕНТРАТОН: ЭКРАНЫ
        elif "5vebczt4" in raw_key:
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"

        # 5. ДЕЦЕНТРАТОН: ПРЕЗЕНТАЦИЯ
        elif "5vebcztc" in raw_key:
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"

        else:
            continue

        send_to_ga4(event_name, item_name, clicks, target_url)

    print("\nГотово! Все 5 категорий отправлены как активные сессии в GA4.")

except Exception as e:
    print(f"Ошибка: {e}")
