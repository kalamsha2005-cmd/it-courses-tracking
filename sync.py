import os
import requests
import json
import idna

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-CMX1EDFBSM"
GA4_API_SECRET = "9AGO30IhQgyEnyioiZi9aA"

STATE_FILE = "state.json"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# 6 курсов Astana Hub
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

# Чтение предыдущего состояния кликов
last_state = {}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            last_state = json.load(f)
    except Exception:
        last_state = {}

session = requests.Session()

try:
    print("Получение данных из Dub.co...")
    res = session.get("https://api.dub.co/links", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co: {res.status_code}")
        exit()

    links = res.json()
    ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    current_state = {}
    is_first_run = len(last_state) == 0

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_key = decode_puny(raw_key)
        target_url = item.get("url", "").lower()
        clicks = item.get("clicks", 0)

        current_state[raw_key] = clicks

        # 1. ПАПКА: 6 курсов Astana Hub
        if raw_key in COURSES_TITLES:
            event_name = "astanahub_courses"
            item_name = COURSES_TITLES[raw_key]

        # 2. ПАПКА: Decentrathon 6.0
        elif "decentrathon" in target_url or "децентр" in decoded_key or "vj" in raw_key.lower():
            if "экран" in decoded_key or "vj" in raw_key.lower():
                event_name = "decentrathon_screens"
                item_name = "Decentrathon (Экраны хаба)"
            else:
                event_name = "decentrathon_presentation"
                item_name = "Decentrathon (Презентация)"

        # 3. ПАПКА: PDF-каталог
        elif "drive.google.com" in target_url or "пдф" in decoded_key or "ise" in raw_key.lower():
            if "экран" in decoded_key or "ise" in raw_key.lower():
                event_name = "catalog_screens"
                item_name = "Каталог PDF (Экраны хаба)"
            else:
                event_name = "catalog_presentation"
                item_name = "Каталог PDF (Презентация)"

        # Резервный случай
        else:
            event_name = "other_clicks"
            item_name = raw_key

        # Подсчет количества событий для отправки
        prev_clicks = last_state.get(raw_key, 0)
        if is_first_run:
            # При первом запуске отправляем фактические клики, но минимум 1 для регистрации строки
            events_to_send = max(clicks, 1)
        else:
            # В последующих запусках шлем только чистую дельту новых кликов
            events_to_send = max(0, clicks - prev_clicks)

        if events_to_send > 0:
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

            for _ in range(events_to_send):
                session.post(ga4_url, json=payload, timeout=5)

            print(f"Отправлено: [{event_name}] {item_name} -> {events_to_send} соб.")
        else:
            print(f"Без новых кликов: [{event_name}] {item_name} (всего {clicks})")

    # Сохраняем состояние
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)

    print("Синхронизация успешно завершена!")

except Exception as e:
    print(f"Ошибка: {e}")
