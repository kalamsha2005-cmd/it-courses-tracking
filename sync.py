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

# Четкие названия событий для курсов (как было раньше)
COURSES_MAP = {
    "hub-pe": "course_prompt_engineering",
    "hub-nlc": "course_nocode_lowcode",
    "hub-ss": "course_startup_school",
    "hub-sa": "course_startup_academy",
    "hub-bc": "course_beta_career",
    "hub-fs": "course_freelance_school"
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
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_to_ga4(event_name, count, target_url):
    for i in range(count):
        payload = {
            "client_id": f"client_{abs(hash(event_name + str(i))) % 1000000}",
            "events": [{
                "name": event_name,
                "params": {
                    "destination_url": target_url
                }
            }]
        }
        session.post(ga4_url, json=payload, timeout=5)
    print(f"-> Отправлено [{event_name}]: {count} соб.")

try:
    print("Получаем данные из Dub.co...")
    res = session.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit()

    links = res.json()

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_key = decode_puny(raw_key)
        target_url = item.get("url", "").lower()
        clicks = item.get("clicks", 0)

        # 1. Курсы Astana Hub (каждый отдельной строкой)
        if raw_key in COURSES_MAP:
            event_name = COURSES_MAP[raw_key]

        # 2. Decentrathon 6.0
        elif "decentrathon" in target_url or "децентр" in decoded_key or "vj" in raw_key.lower():
            if "экран" in decoded_key or "vj" in raw_key.lower():
                event_name = "decentrathon_screens"
            else:
                event_name = "decentrathon_presentation"

        # 3. ЛМС Каталог курсов (PDF)
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "ise" in raw_key.lower() or "лм" in decoded_key:
            if "экран" in decoded_key or "ise" in raw_key.lower():
                event_name = "catalog_screens"
            else:
                event_name = "catalog_presentation"

        else:
            event_name = f"click_{raw_key}"

        # Отправляем фактическое количество кликов (или минимум 1, чтобы строка сразу появилась)
        count_to_send = max(clicks, 1)
        send_to_ga4(event_name, count_to_send, item.get("url", ""))

    print("Все 10 событий успешно отправлены в GA4!")

except Exception as e:
    print(f"Ошибка: {e}")
