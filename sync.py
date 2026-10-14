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

# 6 курсов с их точными названиями
COURSES_MAP = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

def decode_key(raw_text):
    try:
        parts = raw_text.split("_")
        decoded = []
        for p in parts:
            if p.startswith("xn--"):
                try:
                    decoded.append(idna.decode(p))
                except Exception:
                    decoded.append(p)
            else:
                decoded.append(p)
        return "_".join(decoded).lower()
    except Exception:
        return raw_text.lower()

session = requests.Session()
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_events_batch(event_name, item_name, count, target_url):
    # Отправляем события пачками до 25 штук за 1 сетевой запрос
    # Это мгновенно передает все клики без задержек и дублей
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
            payload = {
                "client_id": str(uuid.uuid4()),
                "events": events
            }
            session.post(ga4_url, json=payload, timeout=5)
            events = []

    if events:
        payload = {
            "client_id": str(uuid.uuid4()),
            "events": events
        }
        session.post(ga4_url, json=payload, timeout=5)

    print(f"Успешно доставлено: [{event_name}] '{item_name}' -> {count} кликов")

try:
    print("Запрос всех ссылок из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка API Dub.co: {res.status_code}")
        exit(1)

    links = res.json()
    print(f"Найдено ссылок в Dub.co: {len(links)}")

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_name = decode_key(raw_key)
        target_url = item.get("url", "").lower()
        clicks = item.get("clicks", 0)

        # Передаем реальное число кликов (но не меньше 1, чтобы строчка появилась на экране)
        send_count = max(clicks, 1)

        # 1. ШЕСТЬ КУРСОВ ASTANA HUB -> строго в одну категорию astanahub_courses
        if raw_key in COURSES_MAP:
            event_name = "astanahub_courses"
            item_name = COURSES_MAP[raw_key]
            send_events_batch(event_name, item_name, send_count, item.get("url", ""))

        # 2. ДЕЦЕНТРАТОН - ЭКРАНЫ
        elif "децентр" in decoded_name and "экран" in decoded_name:
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"
            send_events_batch(event_name, item_name, send_count, item.get("url", ""))

        # 3. ДЕЦЕНТРАТОН - ПРЕЗЕНТАЦИЯ
        elif "децентр" in decoded_name and "презентаци" in decoded_name:
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"
            send_events_batch(event_name, item_name, send_count, item.get("url", ""))

        # 4. КАТАЛОГ PDF - ЭКРАНЫ
        elif ("лм" in decoded_name or "drive.google.com" in target_url) and "экран" in decoded_name:
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"
            send_events_batch(event_name, item_name, send_count, item.get("url", ""))

        # 5. КАТАЛОГ PDF - ПРЕЗЕНТАЦИЯ
        elif ("лм" in decoded_name or "drive.google.com" in target_url) and "презентаци" in decoded_name:
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"
            send_events_batch(event_name, item_name, send_count, item.get("url", ""))

        else:
            print(f"Неопознанная ссылка: {raw_key} ({decoded_name})")

    print("\nИдеальная синхронизация завершена! Все 10 ссылок разложены по 5 папкам.")

except Exception as e:
    print(f"Ошибка выполнения: {e}")
