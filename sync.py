import os
import requests
import json
import idna
import uuid

DUB_API_KEY = "dub_YcT0ptmsLS3CJgZeL6ZL1iKN"
GA4_MEASUREMENT_ID = "G-CMX1EDFBSM"
GA4_API_SECRET = "9AGO30IhQgyEnyioiZi9aA"

headers_dub = {
    "Authorization": f"Bearer {DUB_API_KEY}"
}

# Функция для декодирования Punycode (русских букв) в обычный текст
def decode_dub_key(text):
    if not text:
        return ""
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

session = requests.Session()
ga4_url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

def send_to_ga4(event_name, item_name, count, target_url):
    events = []
    for _ in range(count):
        events.append({
            "name": event_name,
            "params": {
                "course_name": item_name,
                "item_name": item_name,
                "destination_url": target_url
            }
        })
        if len(events) == 25:
            session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)
            events = []

    if events:
        session.post(ga4_url, json={"client_id": str(uuid.uuid4()), "events": events}, timeout=5)

    print(f"[{event_name}] '{item_name}' -> отправлено кликов: {count}")

try:
    print("Получение данных из Dub.co...")
    res = session.get("https://api.dub.co/links?limit=50", headers=headers_dub, timeout=10)
    if res.status_code != 200:
        print(f"Ошибка Dub.co API: {res.status_code}")
        exit(1)

    links = res.json()
    print(f"Найдено ссылок: {len(links)}")

    summary = {
        "catalog_screens": 0,
        "catalog_presentation": 0,
        "decentrathon_screens": 0,
        "decentrathon_presentation": 0,
        "astanahub_courses": 0
    }

    for item in links:
        raw_key = item.get("key", "").strip()
        decoded_key = decode_dub_key(raw_key)
        target_url = item.get("url", "").strip()
        clicks = max(item.get("clicks", 0), 1)

        # -------------------------------------------------------------
        # 1) КАТАЛОГ PDF: ЭКРАНЫ
        # -------------------------------------------------------------
        if "лмс_курсы_кьар_на_пдф_экраны" in decoded_key or ("лмс" in decoded_key and "экран" in decoded_key):
            event_name = "catalog_screens"
            item_name = "Каталог PDF (Экраны хаба)"

        # -------------------------------------------------------------
        # 2) КАТАЛОГ PDF: ДЛЯ ПРЕЗЕНТАЦИЙ
        # -------------------------------------------------------------
        elif "лмс_курсы_кьар_на_пдф_для_презентации" in decoded_key or ("лмс" in decoded_key and "презентаци" in decoded_key):
            event_name = "catalog_presentation"
            item_name = "Каталог PDF (Презентация)"

        # -------------------------------------------------------------
        # 3) ДЕЦЕНТРАТОН 6.0: ЭКРАНЫ
        # -------------------------------------------------------------
        elif "децентра_6.0_кьар_на_рег_экраны" in decoded_key or ("децентр" in decoded_key and "экран" in decoded_key):
            event_name = "decentrathon_screens"
            item_name = "Decentrathon (Экраны хаба)"

        # -------------------------------------------------------------
        # 4) ДЕЦЕНТРАТОН 6.0: ПРЕЗЕНТАЦИИ
        # -------------------------------------------------------------
        elif "децентра_6.0_кьар_на_рег_презентации" in decoded_key or ("децентр" in decoded_key and "презентаци" in decoded_key):
            event_name = "decentrathon_presentation"
            item_name = "Decentrathon (Презентация)"

        # -------------------------------------------------------------
        # 5–10) 6 КУРСОВ ASTANA HUB -> СТРОГО В ПАПКУ astanahub_courses
        # -------------------------------------------------------------
        elif raw_key == "hub-pe":
            event_name = "astanahub_courses"
            item_name = "Prompt Engineering"

        elif raw_key == "hub-nlc":
            event_name = "astanahub_courses"
            item_name = "No-code / Low-code"

        elif raw_key == "hub-ss":
            event_name = "astanahub_courses"
            item_name = "Startup School"

        elif raw_key == "hub-sa":
            event_name = "astanahub_courses"
            item_name = "Startup Academy"

        elif raw_key == "hub-bc":
            event_name = "astanahub_courses"
            item_name = "Beta Career"

        elif raw_key == "hub-fs":
            event_name = "astanahub_courses"
            item_name = "Freelance School"

        else:
            print(f"Неизвестная ссылка: {raw_key} ({decoded_key})")
            continue

        send_to_ga4(event_name, item_name, clicks, target_url)
        summary[event_name] += clicks

    print("\nИТОГИ РАСПРЕДЕЛЕНИЯ ПО 5 ПАПКАМ:")
    for k, v in summary.items():
        print(f" -> {k}: {v} кликов")

except Exception as e:
    print(f"Ошибка выполнения: {e}")
