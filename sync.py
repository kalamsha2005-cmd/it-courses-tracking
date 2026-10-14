import os
import requests
import json
import idna

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-T4QCCV5D0Z"
GA4_API_SECRET = "XBMxi-AOQHCvvq2RI8SHug"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# 6 курсов: латинский ключ для GA4 и красивое русское название
COURSES_MAP = {
    "hub-pe": ("course_prompt_engineering", "Prompt Engineering"),
    "hub-nlc": ("course_nocode_lowcode", "No-code / Low-code"),
    "hub-ss": ("course_startup_school", "Startup School"),
    "hub-sa": ("course_startup_academy", "Startup Academy"),
    "hub-bc": ("course_beta_career", "Beta Career"),
    "hub-fs": ("course_freelance_school", "Freelance School")
}

def decode_punycode(raw_key):
    try:
        if raw_key.startswith("xn--"):
            return idna.decode(raw_key).lower()
        return raw_key.lower()
    except Exception:
        return raw_key.lower()

try:
    print("Получение данных из Dub.co...")
    res = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit()

    links = res.json()
    ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded = decode_punycode(raw_key)
        target = item.get("url", "")
        clicks = item.get("clicks", 0)

        # 1. Ветка: Decentrathon 6.0
        if "децентр" in decoded or "decentrathon" in target:
            if "экран" in decoded or "screen" in decoded:
                event_name = "decentrathon_screens"
                label = "Decentrathon (Экраны хаба)"
            else:
                event_name = "decentrathon_presentation"
                label = "Decentrathon (Презентация)"

        # 2. Ветка: PDF-каталог
        elif "пдф" in decoded or "курсы" in decoded or "drive.google.com" in target:
            if "экран" in decoded or "screen" in decoded:
                event_name = "catalog_screens"
                label = "Каталог PDF (Экраны хаба)"
            else:
                event_name = "catalog_presentation"
                label = "Каталог PDF (Презентация)"

        # 3. Ветка: 6 курсов Astana Hub
        else:
            if raw_key in COURSES_MAP:
                event_name, label = COURSES_MAP[raw_key]
            else:
                clean_name = raw_key.replace("-", "_")
                event_name = f"course_{clean_name}"
                label = raw_key

        payload = {
            "client_id": f"aktobe_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": {
                    "item_name": label,
                    "destination_url": target
                }
            }]
        }
        requests.post(ga4_url, json=payload, timeout=5)
        print(f"Отправлено: {event_name} -> {label}")

    print("Все 10 ссылок успешно синхронизированы!")

except Exception as e:
    print(f"Ошибка: {e}")
