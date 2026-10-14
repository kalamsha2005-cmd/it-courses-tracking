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

# 1. Четкие читаемые названия для курсов
COURSE_MAP = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code School",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

def decode_key(raw_key):
    """Декодирует xn-- в нормальные русские буквы"""
    try:
        if raw_key.startswith("xn--"):
            return idna.decode(raw_key).lower()
        return raw_key.lower()
    except Exception:
        return raw_key.lower()

try:
    print("Запрос ссылок из Dub.co...")
    dub_resp = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if dub_resp.status_code != 200:
        print(f"Ошибка Dub.co: {dub_resp.status_code}")
        exit()

    links_data = dub_resp.json()
    ga4_endpoint = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links_data:
        raw_key = item.get("key", "").strip()
        decoded_name = decode_key(raw_key)
        target_url = item.get("url", "")
        clicks = item.get("clicks", 0)

        # 1. Ссылки Decentrathon 6.0
        if "децентр" in decoded_name or "decentrathon" in target_url:
            event_name = "decentrathon_registration"
            is_screen = ("экран" in decoded_name or "screen" in decoded_name)
            channel = "Экраны хаба" if is_screen else "Презентация"
            params = {
                "campaign_name": "Decentrathon 6.0",
                "traffic_channel": channel,
                "destination_url": target_url
            }

        # 2. Ссылки на PDF-каталог (Google Диск)
        elif "пдф" in decoded_name or "курсы" in decoded_name or "drive.google.com" in target_url:
            event_name = "catalog_view"
            is_screen = ("экран" in decoded_name or "screen" in decoded_name)
            channel = "Экраны хаба" if is_screen else "Презентация"
            params = {
                "campaign_name": "Каталог курсов (PDF)",
                "traffic_channel": channel,
                "destination_url": target_url
            }

        # 3. Шесть курсов Astana Hub
        else:
            event_name = "course_click"
            clean_title = COURSE_MAP.get(raw_key, raw_key)
            params = {
                "course_title": clean_title,
                "destination_url": target_url
            }

        # Отправляем клики (если кликов 0, шлем 1 для отображения в GA4)
        times_to_send = max(clicks, 1)

        payload = {
            "client_id": f"dub_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": params
            }]
        }
        requests.post(ga4_endpoint, json=payload, timeout=5)
        print(f"Отправлено: {event_name} -> {decoded_name}")

    print("Синхронизация завершена успешно.")

except Exception as e:
    print(f"Ошибка: {e}")
