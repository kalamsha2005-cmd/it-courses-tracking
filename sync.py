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

# 6 курсов Astana Hub: привязка ключа к красивому названию
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
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_to_ga4(event_name, item_name, count, target_url):
    for i in range(count):
        payload = {
            "client_id": f"client_{abs(hash(item_name + str(i))) % 1000000}",
            "events": [{
                "name": event_name,
                "params": {
                    "course_name": item_name,
                    "item_name": item_name,
                    "destination_url": target_url
                }
            }]
        }
        session.post(ga4_url, json=payload, timeout=5)
    print(f"-> [{event_name}] {item_name} отправлено {count} раз")

try:
    print("Получаем ссылки из Dub.co...")
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
        # Отправляем фактические клики, но минимум 1, чтобы строка железно была видна в отчете
        to_send = max(clicks, 1)

        # 1. ЕДИНАЯ ПАПКА ДЛЯ 6 КУРСОВ
        if raw_key in COURSES_TITLES:
            event_name = "astanahub_courses"
            item_name = COURSES_TITLES[raw_key]
            send_to_ga4(event_name, item_name, to_send, item.get("url", ""))

        # 2. ДЕЦЕНТРАТОН: ЭКРАНЫ
        elif "децентр" in decoded_key and "экран" in decoded_key or "vj" in raw_key.lower():
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"
            send_to_ga4(event_name, item_name, to_send, item.get("url", ""))

        # 3. ДЕЦЕНТРАТОН: ПРЕЗЕНТАЦИЯ
        elif "децентр" in decoded_key or "decentrathon" in target_url:
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"
            send_to_ga4(event_name, item_name, to_send, item.get("url", ""))

        # 4. КАТАЛОГ PDF: ЭКРАНЫ
        elif ("drive.google.com" in target_url or "пдф" in decoded_key or "ise" in raw_key.lower()) and ("экран" in decoded_key or "ise" in raw_key.lower()):
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"
            send_to_ga4(event_name, item_name, to_send, item.get("url", ""))

        # 5. КАТАЛОГ PDF: ПРЕЗЕНТАЦИЯ
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "презентаци" in decoded_key or "лм" in decoded_key:
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"
            send_to_ga4(event_name, item_name, to_send, item.get("url", ""))

    print("Все 5 категорий успешно структурированы и отправлены в GA4!")

except Exception as e:
    print(f"Ошибка: {e}")
