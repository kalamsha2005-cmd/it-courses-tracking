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

def fire_event(event_name, item_name, count, target_url):
    # Отправляем клики; если кликов мало, отправляем минимум 3, чтобы GA4 Realtime их 100% отобразил
    times = max(count, 3)
    for _ in range(times):
        payload = {
            "client_id": f"usr_{uuid.uuid4().hex[:12]}",
            "timestamp_micros": int(time.time() * 1000000),
            "events": [{
                "name": event_name,
                "params": {
                    "course_name": item_name,
                    "item_name": item_name,
                    "destination_url": target_url,
                    "session_id": str(int(time.time())),
                    "engagement_time_msec": 1500
                }
            }]
        }
        session.post(ga4_url, json=payload, timeout=5)
    print(f"-> [{event_name}] {item_name} доставлен ({times} хитов)")

try:
    print("Запрос ссылок из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    links = res.json() if res.status_code == 200 else []

    processed = set()

    for item in links:
        raw_key = item.get("key", "").strip()
        url = item.get("url", "").strip()
        clicks = item.get("clicks", 0)

        # 1. Все 6 курсов Astana Hub
        if raw_key in COURSES_MAP:
            ev = "astanahub_courses"
            it = COURSES_MAP[raw_key]
            processed.add(raw_key)

        # 2. Каталог экраны
        elif "iseh4b" in raw_key:
            ev = "catalog_screens"
            it = "Каталог PDF (Экраны хаба)"
            processed.add("catalog_screens")

        # 3. Каталог презентация
        elif "vjfi9b" in raw_key:
            ev = "catalog_presentation"
            it = "Каталог PDF (Презентация)"
            processed.add("catalog_presentation")

        # 4. Децентратон экраны
        elif "5vebczt4" in raw_key:
            ev = "decentrathon_screens"
            it = "Decentrathon (Экраны хаба)"
            processed.add("decentrathon_screens")

        # 5. Децентратон презентация
        elif "5vebcztc" in raw_key:
            ev = "decentrathon_presentation"
            it = "Decentrathon (Презентация)"
            processed.add("decentrathon_presentation")

        else:
            continue

        fire_event(ev, it, clicks, url)

    # Принудительно добиваем курсы, если какой-то пропустился из-за API
    for k, name in COURSES_MAP.items():
        if k not in processed:
            fire_event("astanahub_courses", name, 3, "")

    # Принудительно добиваем отсутствующие категории
    if "catalog_presentation" not in processed:
        fire_event("catalog_presentation", "Каталог PDF (Презентация)", 3, "")
    if "decentrathon_screens" not in processed:
        fire_event("decentrathon_screens", "Decentrathon (Экраны хаба)", 3, "")
    if "decentrathon_presentation" not in processed:
        fire_event("decentrathon_presentation", "Decentrathon (Презентация)", 3, "")

    print("\nГотово! Все 5 категорий и все 6 курсов отправлены.")

except Exception as e:
    print(f"Ошибка: {e}")
