import os
import requests
import json
import idna
import uuid

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-CMX1EDFBSM"
GA4_API_SECRET = "9AGO30IhQgyEnyioiZi9aA"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# 6 курсов Astana Hub -> пойдут строго внутрь astanahub_courses
COURSES = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

def decode_punycode(text):
    try:
        parts = text.split("_")
        res = []
        for p in parts:
            if p.startswith("xn--"):
                try:
                    res.append(idna.decode(p))
                except Exception:
                    res.append(p)
            else:
                res.append(p)
        return "_".join(res).lower()
    except Exception:
        return text.lower()

session = requests.Session()
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_batch(event_name, item_name, count, url=""):
    events = []
    for _ in range(count):
        events.append({
            "name": event_name,
            "params": {
                "course_name": item_name,
                "item_name": item_name,
                "destination_url": url
            }
        })
        if len(events) == 25:
            session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)
            events = []
    if events:
        session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)
    print(f"[{event_name}] -> {item_name}: отправлено {count}")

try:
    print("Получаем все ссылки из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit(1)

    links = res.json()
    print(f"Всего ссылок получено: {len(links)}")

    categories_count = {
        "catalog_screens": 0,
        "catalog_presentation": 0,
        "decentrathon_screens": 0,
        "decentrathon_presentation": 0,
        "astanahub_courses": 0
    }

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_name = decode_punycode(raw_key)
        target_url = item.get("url", "").lower()
        clicks = max(item.get("clicks", 0), 1)

        # 1. ШЕСТЬ КУРСОВ (ЕДИНАЯ ПАПКА)
        if raw_key in COURSES:
            event_name = "astanahub_courses"
            item_name = COURSES[raw_key]

        # 2. ДЕЦЕНТРАТОН - ЭКРАНЫ
        elif "децентр" in decoded_name and "экран" in decoded_name:
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"

        # 3. ДЕЦЕНТРАТОН - ПРЕЗЕНТАЦИЯ
        elif "децентр" in decoded_name and ("презентаци" in decoded_name or "пер" in decoded_name):
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"

        # 4. КАТАЛОГ PDF - ЭКРАНЫ
        elif ("лм" in decoded_name or "drive.google.com" in target_url) and "экран" in decoded_name:
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"

        # 5. КАТАЛОГ PDF - ПРЕЗЕНТАЦИЯ
        elif ("лм" in decoded_name or "drive.google.com" in target_url) and ("презентаци" in decoded_name or "для" in decoded_name):
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"

        else:
            print(f"Пропуск нераспознанной: {raw_key} ({decoded_name})")
            continue

        send_batch(event_name, item_name, clicks, item.get("url", ""))
        categories_count[event_name] += clicks

    print("\nИтог синхронизации по категориям:")
    for cat, total in categories_count.items():
        print(f" - {cat}: {total} кликов")

except Exception as e:
    print(f"Ошибка: {e}")
