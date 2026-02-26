import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests

SEARCH_URL = "https://www.sahibinden.com/bmw-3-serisi-320i-ed?sorting=date_desc"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SEEN_FILE = "seen_ids.json"

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
    first_run = not os.path.exists(SEEN_FILE)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    try:
        driver.get(SEARCH_URL)
        time.sleep(5)
        items = driver.find_elements(By.CSS_SELECTOR, "tr.searchResultsItem")
        if not items:
            print("İlan bulunamadı.")
            send_telegram("⚠️ Sahibinden'de ilan bulunamadı veya erişim engellendi.")
            return
        seen = load_seen()
        new_items = []
        for item in items:
            try:
                ilan_id = item.get_attribute("data-id")
                if not ilan_id:
                    continue
                if not first_run and ilan_id in seen:
                    continue
                try:
                    baslik = item.find_element(By.CSS_SELECTOR, "td.searchResultsTitleValue a").text.strip()
                except:
                    baslik = "Bilinmiyor"
                try:
                    fiyat = item.find_element(By.CSS_SELECTOR, "td.searchResultsPriceValue").text.strip()
                except:
                    fiyat = "Bilinmiyor"
                try:
                    tarih = item.find_element(By.CSS_SELECTOR, "td.searchResultsDateValue").text.strip()
                except:
                    tarih = "Bilinmiyor"
                try:
                    link = item.find_element(By.CSS_SELECTOR, "td.searchResultsTitleValue a").get_attribute("href")
                except:
                    link = ""
                new_items.append((ilan_id, baslik, fiyat, tarih, link))
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
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
