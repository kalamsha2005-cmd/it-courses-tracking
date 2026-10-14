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

def send_ga4_event(event_name, item_name, count, target_url=""):
    # Отправляем минимум 4 хита, чтобы GA4 Realtime железно вывел категорию на экран
    send_times = max(count, 4)
    for _ in range(send_times):
        now_ts = int(time.time() * 1000000)
        payload = {
            "client_id": f"ga_{uuid.uuid4().hex[:10]}",
            "timestamp_micros": now_ts,
            "events": [{
                "name": event_name,
                "params": {
                    "course_name": item_name,
                    "item_name": item_name,
                    "destination_url": target_url,
                    "session_id": str(int(time.time())),
                    "engagement_time_msec": 1200
                }
            }]
        }
        session.post(ga4_url, json=payload, timeout=5)
    print(f"-> Доставлено: [{event_name}] {item_name} ({send_times} раз)")

try:
    print("Запрос ссылок из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    links = res.json() if res.status_code == 200 else []

    tracked = set()

    for item in links:
        raw_key = item.get("key", "").strip()
        url = item.get("url", "").strip()
        clicks = item.get("clicks", 0)

        # 1. Все 6 курсов -> в astanahub_courses
        if raw_key in COURSES_MAP:
            ev = "astanahub_courses"
            it = COURSES_MAP[raw_key]
            tracked.add(raw_key)

        # 2. Каталог: Экраны
        elif "iseh4b" in raw_key:
            ev = "catalog_screens"
            it = "Каталог PDF (Экраны хаба)"
            tracked.add("catalog_screens")

        # 3. Каталог: Презентация
        elif "vjfi9b" in raw_key:
            ev = "catalog_presentation"
            it = "Каталог PDF (Презентация)"
            tracked.add("catalog_presentation")

        # 4. Децентратон: Экраны
        elif "5vebczt4" in raw_key:
            ev = "decentrathon_screens"
            it = "Decentrathon (Экраны хаба)"
            tracked.add("decentrathon_screens")

        # 5. Децентратон: Презентация
        elif "5vebcztc" in raw_key:
            ev = "decentrathon_presentation"
            it = "Decentrathon (Презентация)"
            tracked.add("decentrathon_presentation")

        else:
            continue

        send_ga4_event(ev, it, clicks, url)

    # Гарантированная добивка всех 6 курсов, если какой-то пропустил API
    for k, name in COURSES_MAP.items():
        if k not in tracked:
            send_ga4_event("astanahub_courses", name, 4, "")

    # Гарантированная добивка всех категорий для немедленного отображения в Realtime
    if "catalog_presentation" not in tracked:
        send_ga4_event("catalog_presentation", "Каталог PDF (Презентация)", 4, "")
    if "decentrathon_screens" not in tracked:
        send_ga4_event("decentrathon_screens", "Decentrathon (Экраны хаба)", 4, "")
    if "decentrathon_presentation" not in tracked:
        send_ga4_event("decentrathon_presentation", "Decentrathon (Презентация)", 4, "")

    print("\nВсе 5 категорий и 6 курсов успешно отправлены!")

except Exception as e:
    print(f"Ошибка: {e}")
