import os
import requests
import json
import uuid

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
    events = []
    for _ in range(count):
        events.append({
            "name": event_name,
            "params": {
                "course_name": item_name,
                "item_name": item_name,
                "destination_url": target_url
            }
        })
        if len(events) == 25:
            session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)
            events = []

    if events:
        session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)

    print(f"[{event_name}] '{item_name}' -> отправлено кликов: {count}")

try:
    print("Получение данных из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co API: {res.status_code}")
        exit(1)

    links = res.json()
    print(f"Найдено ссылок: {len(links)}")

    summary = {
        "catalog_screens": 0,
        "catalog_presentation": 0,
        "decentrathon_screens": 0,
        "decentrathon_presentation": 0,
        "astanahub_courses": 0
    }

    for item in links:
        raw_key = item.get("key", "").strip()
        target_url = item.get("url", "").strip().lower()
        clicks = max(item.get("clicks", 0), 1)

        # 1. ШЕСТЬ КУРСОВ ASTANA HUB
        if raw_key in COURSES_MAP:
            event_name = "astanahub_courses"
            item_name = COURSES_MAP[raw_key]

        # 2. КАТАЛОГ PDF: ЭКРАНЫ (хеш iseh4b...)
        elif "iseh4b" in raw_key:
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"

        # 3. КАТАЛОГ PDF: ПРЕЗЕНТАЦИЯ (хеш vjfi9b...)
        elif "vjfi9b" in raw_key:
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"

        # 4. ДЕЦЕНТРАТОН: ЭКРАНЫ (хеш 5vebczt4...)
        elif "5vebczt4" in raw_key:
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"

        # 5. ДЕЦЕНТРАТОН: ПРЕЗЕНТАЦИЯ (хеш 5vebcztc...)
        elif "5vebcztc" in raw_key:
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"

        else:
            print(f"Неизвестная ссылка: {raw_key}")
            continue

        send_to_ga4(event_name, item_name, clicks, item.get("url", ""))
        summary[event_name] += clicks

    print("\nИТОГИ РАСПРЕДЕЛЕНИЯ ПО 5 ПАПКАМ:")
    for k, v in summary.items():
        print(f" -> {k}: {v} кликов")

except Exception as e:
    print(f"Ошибка выполнения: {e}")
