import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random

SEARCH_URL = "https://www.sahibinden.com/bmw-3-serisi-320i-ed?sorting=date_desc"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SEEN_FILE = "seen_ids.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=data)

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def scrape():
    try:
        first_run = not os.path.exists(SEEN_FILE)
        
        session = requests.Session()
        # Önce ana sayfayı ziyaret et
        session.get("https://www.sahibinden.com", headers=HEADERS, timeout=15)
        time.sleep(random.uniform(2, 4))
        
        response = session.get(SEARCH_URL, headers=HEADERS, timeout=15)
        print(f"Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("tr.searchResultsItem")

        if not items:
            print("İlan bulunamadı, ham HTML:")
            print(response.text[:500])
            send_telegram("⚠️ Sahibinden'e bağlanılamadı veya ilan bulunamadı.")
            return

        seen = load_seen()
        new_items = []

        for item in items:
            try:
                ilan_id = item.get("data-id", "")
                if not ilan_id:
                    continue
                if not first_run and ilan_id in seen:
                    continue

                baslik = item.select_one("td.searchResultsTitleValue a")
                fiyat = item.select_one("td.searchResultsPriceValue")
                tarih = item.select_one("td.searchResultsDateValue")
                link_el = item.select_one("td.searchResultsTitleValue a")

                baslik_text = baslik.text.strip() if baslik else "Bilinmiyor"
                fiyat_text = fiyat.text.strip() if fiyat else "Bilinmiyor"
                tarih_text = tarih.text.strip() if tarih else "Bilinmiyor"
                link = "https://www.sahibinden.com" + link_el["href"] if link_el else ""

                new_items.append((ilan_id, baslik_text, fiyat_text, tarih_text, link))
                seen.add(ilan_id)

            except Exception as e:
                print(f"Hata: {e}")
                continue

        if new_items:
            for ilan_id, baslik, fiyat, tarih, link in new_items:
                msg = (
                    f"🚗 <b>Yeni BMW İlanı!</b>\n\n"
                    f"📌 <b>{baslik}</b>\n"
                    f"💰 {fiyat}\n"
                    f"📅 {tarih}\n"
                    f"🔗 <a href='{link}'>İlana Git</a>"
                )
                send_telegram(msg)
                print(f"Bildirim gönderildi: {baslik}")
            save_seen(seen)
        else:
            print("Yeni ilan yok.")
            save_seen(seen)

    except Exception as e:
        print(f"Genel hata: {e}")
        send_telegram(f"⚠️ Script hatası: {e}")

if __name__ == "__main__":
    scrape()
