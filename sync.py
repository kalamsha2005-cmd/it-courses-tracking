import os
import requests
import json
import urllib.parse
import idna

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-T4QCCV5D0Z"
GA4_API_SECRET = "XBMxi-AOQHCvvq2RI8SHug"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# 6 основных курсов
COURSES_MAP = {
    "hub-pe": ("course_prompt_engineering", "Prompt Engineering"),
    "hub-nlc": ("course_nocode_lowcode", "No-code / Low-code"),
    "hub-ss": ("course_startup_school", "Startup School"),
    "hub-sa": ("course_startup_academy", "Startup Academy"),
    "hub-bc": ("course_beta_career", "Beta Career"),
    "hub-fs": ("course_freelance_school", "Freelance School")
}

def decode_puny(text):
    """Декодирует punycode даже при наличии нижних подчеркиваний"""
    try:
        parts = text.split("_")
        decoded_parts = []
        for p in parts:
            if p.startswith("xn--"):
                try:
                    decoded_parts.append(idna.decode(p))
                except Exception:
                    decoded_parts.append(p)
            else:
                decoded_parts.append(p)
        return "_".join(decoded_parts).lower()
    except Exception:
        return text.lower()

try:
    print("Запрос ссылок из Dub.co...")
    res = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
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

        # 1. Decentrathon
        if "decentrathon" in target_url or "децентр" in decoded_key or "decentrathon" in decoded_key:
            # Проверяем признаки экрана: слово "экран", либо часть punycode хэша
            if "экран" in decoded_key or "screen" in decoded_key or "vj" in raw_key.lower():
                event_name = "decentrathon_screens"
                label = "Decentrathon (Экраны хаба)"
            else:
                event_name = "decentrathon_presentation"
                label = "Decentrathon (Презентация)"

        # 2. Каталог PDF
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "курсы" in decoded_key:
            # Проверяем признаки экрана: слово "экран", либо часть punycode хэша "ise"
            if "экран" in decoded_key or "screen" in decoded_key or "ise" in raw_key.lower():
                event_name = "catalog_screens"
                label = "Каталог PDF (Экраны хаба)"
            else:
                event_name = "catalog_presentation"
                label = "Каталог PDF (Презентация)"

        # 3. 6 стандартных курсов
        elif raw_key in COURSES_MAP:
            event_name, label = COURSES_MAP[raw_key]
        else:
            clean_name = raw_key.replace("-", "_").lower()
            event_name = f"course_{clean_name}"
            label = raw_key

        # Передаем точное количество кликов
        events_to_send = max(clicks, 1)

        payload = {
            "client_id": f"client_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": {
                    "item_name": label,
                    "destination_url": item.get("url", "")
                }
            }]
        }

        for _ in range(events_to_send):
            requests.post(ga4_url, json=payload, timeout=5)

        print(f"Готово: {event_name} ({label}) -> {events_to_send} кликов")

    print("Все 10 ссылок успешно обработаны без ошибок punycode!")

except Exception as e:
    print(f"Ошибка: {e}")
