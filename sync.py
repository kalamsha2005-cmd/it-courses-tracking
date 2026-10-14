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

# Словарь для красивых названий курсов
COURSE_NAMES = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code School",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

try:
    dub_resp = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if dub_resp.status_code != 200:
        print(f"Dub.co error: {dub_resp.status_code}")
        exit()

    links_data = dub_resp.json()
    ga4_endpoint = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links_data:
        raw_key = item.get("key", "")
        # Декодируем кириллицу, если она закодирована
        key = urllib.parse.unquote(raw_key).lower()
        clicks = item.get("clicks", 0)
        target_url = item.get("url", "")

        # Определяем события
        if "экраны" in key or "screens" in key:
            event_name = "catalog_view"
            params = {"source": "screens", "campaign": "aktobe_catalog"}
        elif "презентаци" in key or "presentation" in key:
            event_name = "catalog_view"
            params = {"source": "presentation", "campaign": "aktobe_catalog"}
        elif "децентра" in key or "decentrathon" in key:
            event_name = "decentrathon_registration"
            params = {"source": "hub_screens", "campaign": "decentrathon_6.0"}
        else:
            event_name = "course_click"
            clean_name = COURSE_NAMES.get(raw_key.strip(), raw_key)
            params = {"course_title": clean_name, "destination_url": target_url}

        # Отправляем клики (минимум 1 раз, чтобы все 6 курсов появились в списке)
        payload = {
            "client_id": f"dub_auto_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": params
            }]
        }
        requests.post(ga4_endpoint, json=payload, timeout=5)
        print(f"Pushed: {raw_key} -> {event_name}")

    print("Sync completed successfully.")
except Exception as e:
    print(f"Error: {e}")
