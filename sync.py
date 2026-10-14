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

# 6 курсов на чистом русском/английском
COURSES = {
    "hub-pe": "Prompt Engineering",
    "hub-nlc": "No-code / Low-code School",
    "hub-ss": "Startup School",
    "hub-sa": "Startup Academy",
    "hub-bc": "Beta Career",
    "hub-fs": "Freelance School"
}

def clean_key(raw_key):
    try:
        if raw_key.startswith("xn--"):
            return idna.decode(raw_key).lower()
        return raw_key.lower()
    except Exception:
        return raw_key.lower()

try:
    res = requests.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit()

    links = res.json()
    ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded = clean_key(raw_key)
        target = item.get("url", "")
        clicks = item.get("clicks", 0)

        # 1. ВЕТКА: Decentrathon 6.0
        if "децентр" in decoded or "decentrathon" in target:
            event_name = "decentrathon_registration"
            channel = "Экраны хаба" if ("экран" in decoded or "screen" in decoded) else "Презентация"
            params = {
                "campaign": "Decentrathon 6.0",
                "source": channel,
                "medium": "QR-код",
                "content": "Регистрация на хакатон"
            }

        # 2. ВЕТКА: Каталог курсов (сканирование QR-кода на PDF)
        elif "пдф" in decoded or "курсы" in decoded or "drive.google.com" in target:
            event_name = "catalog_view"
            channel = "Экраны хаба" if ("экран" in decoded or "screen" in decoded) else "Презентация"
            params = {
                "campaign": "Каталог курсов",
                "source": channel,
                "medium": "QR-код",
                "content": "Открытие PDF-каталога"
            }

        # 3. ВЕТКА: Клики внутри PDF по конкретным курсам
        else:
            event_name = "course_click"
            course_title = COURSES.get(raw_key, raw_key)
            params = {
                "campaign": "Каталог курсов",
                "source": "PDF-каталог",
                "medium": "Кнопка в документе",
                "item_name": course_title,
                "content": course_title
            }

        # Отправляем клики
        payload = {
            "client_id": f"user_{abs(hash(raw_key)) % 1000000}",
            "events": [{
                "name": event_name,
                "params": params
            }]
        }
        requests.post(ga4_url, json=payload, timeout=5)
        print(f"Синхронизировано: {params['campaign']} -> {params['source']} ({params.get('content')})")

    print("Все данные успешно разложены по структуре!")

except Exception as e:
    print(f"Ошибка: {e}")
