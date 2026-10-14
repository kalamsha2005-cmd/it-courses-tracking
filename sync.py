import os
import requests
import json
import urllib.parse

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-T4QCCV5D0Z"
GA4_API_SECRET = "XBMxi-AOQHCvvq2RI8SHug"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# 6 курсов Astana Hub: привязка по ключу в Dub.co
COURSES_MAP = {
    "hub-pe": ("course_prompt_engineering", "Prompt Engineering"),
    "hub-nlc": ("course_nocode_lowcode", "No-code / Low-code"),
    "hub-ss": ("course_startup_school", "Startup School"),
    "hub-sa": ("course_startup_academy", "Startup Academy"),
    "hub-bc": ("course_beta_career", "Beta Career"),
    "hub-fs": ("course_freelance_school", "Freelance School")
}

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
        # Корректно расшифровываем любые русские символы
        decoded_key = urllib.parse.unquote(raw_key).lower()
        target_url = item.get("url", "").lower()
        clicks = item.get("clicks", 0)

        # 1. Если ссылка ведёт на Decentrathon
        if "decentrathon" in target_url or "децентр" in decoded_key:
            if "экран" in decoded_key or "screen" in decoded_key:
                event_name = "decentrathon_screens"
                label = "Decentrathon (Экраны хаба)"
            else:
                event_name = "decentrathon_presentation"
                label = "Decentrathon (Презентация)"

        # 2. Если ссылка ведёт на Google Диск с каталогом PDF
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "каталог" in decoded_key:
            if "экран" in decoded_key or "screen" in decoded_key:
                event_name = "catalog_screens"
                label = "Каталог PDF (Экраны хаба)"
            else:
                event_name = "catalog_presentation"
                label = "Каталог PDF (Презентация)"

        # 3. Курсы Astana Hub
        else:
            if raw_key in COURSES_MAP:
                event_name, label = COURSES_MAP[raw_key]
            else:
                clean_name = raw_key.replace("-", "_").lower()
                event_name = f"course_{clean_name}"
                label = raw_key

        # Определяем, сколько событий отправить в GA4:
        # Если в Dub.co есть реальные клики — отправляем именно их количество!
        # Если кликов пока 0 — отправляем 1 тестовый, чтобы событие появилось в списке аналитики.
        events_to_send = max(clicks, 1)

        for _ in range(events_to_send):
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
            requests.post(ga4_url, json=payload, timeout=5)

        print(f"Синхронизировано: {label} [{event_name}] — кликов учтено: {events_to_send}")

    print("Синхронизация завершена без ошибок!")

except Exception as e:
    print(f"Ошибка при выполнении: {e}")
