import os
import requests
import json
import idna

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-CMX1EDFBSM"
GA4_API_SECRET = "9AGO30IhQgyEnyioiZi9aA"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

COURSES_TITLES = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

def decode_puny(text):
    try:
        parts = text.split("_")
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
        return text.lower()

session = requests.Session()

try:
    print("Получение данных из Dub.co...")
    res = session.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit()

    links = res.json()
    ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_key = decode_puny(raw_key)
        target_url = item.get("url", "").lower()
        clicks = item.get("clicks", 0)

        # 1. 6 курсов Astana Hub
        if raw_key in COURSES_TITLES:
            event_name = "astanahub_courses"
            item_name = COURSES_TITLES[raw_key]

        # 2. Decentrathon
        elif "decentrathon" in target_url or "децентр" in decoded_key or "vj" in raw_key.lower():
            if "экран" in decoded_key or "vj" in raw_key.lower():
                event_name = "decentrathon_screens"
                item_name = "Decentrathon (Экраны хаба)"
            else:
                event_name = "decentrathon_presentation"
                item_name = "Decentrathon (Презентация)"

        # 3. PDF-каталог
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "ise" in raw_key.lower():
            if "экран" in decoded_key or "ise" in raw_key.lower():
                event_name = "catalog_screens"
                item_name = "Каталог PDF (Экраны хаба)"
            else:
                event_name = "catalog_presentation"
                item_name = "Каталог PDF (Презентация)"

        # Резерв
        else:
            event_name = "other_clicks"
            item_name = raw_key

        # Шлем ровно столько кликов, сколько есть в Dub.co (или минимум 1, чтобы строчка появилась)
        count_to_send = max(clicks, 1)

        payload = {
            "client_id": f"client_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": {
                    "course_name": item_name,
                    "item_name": item_name,
                    "destination_url": item.get("url", "")
                }
            }]
        }

        for _ in range(count_to_send):
            session.post(ga4_url, json=payload, timeout=5)

        print(f"Отправлено в GA4: [{event_name}] {item_name} -> {count_to_send}")

    print("Все ссылки принудительно доставлены!")

except Exception as e:
    print(f"Ошибка: {e}")
