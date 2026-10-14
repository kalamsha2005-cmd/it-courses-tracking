import os
import requests
import json

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-T4QCCV5D0Z"
GA4_API_SECRET = "XBMxi-AOQHCvvq2RI8SHug"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

try:
    dub_resp = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if dub_resp.status_code != 200:
        print(f"Dub.co error: {dub_resp.status_code}")
        exit()

    links_data = dub_resp.json()
    ga4_endpoint = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links_data:
        key = item.get("key", "")
        clicks = item.get("clicks", 0)
        target_url = item.get("url", "")
        
        if "экраны" in key.lower() or "screens" in key.lower():
            event_name = "catalog_view"
            params = {"source": "screens", "campaign": "aktobe_catalog"}
        elif "презентаци" in key.lower() or "presentation" in key.lower():
            event_name = "catalog_view"
            params = {"source": "presentation", "campaign": "aktobe_catalog"}
        elif "децентра" in key.lower():
            event_name = "decentrathon_registration"
            params = {"source": "hub_screens", "campaign": "decentrathon_6.0"}
        else:
            event_name = "course_click"
            params = {"course_title": key, "destination_url": target_url}

        # Отправляем клики
        if clicks > 0:
            payload = {
                "client_id": f"dub_auto_{abs(hash(key)) % 1000000}",
                "events": [{
                    "name": event_name,
                    "params": params
                }]
            }
            requests.post(ga4_endpoint, json=payload, timeout=5)
            print(f"Pushed: {key} -> {event_name}")

    print("Sync completed successfully.")
except Exception as e:
    print(f"Error: {e}")
