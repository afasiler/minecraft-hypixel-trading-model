#!/usr/bin/env python3
"""
Hypixel Bazaar Veri Toplayıcı (v2 - gzip sıkıştırmalı)
- Dakikada bir tüm bazaar verisini çeker.
- Başarılı çekimlerde JSON dosyası gzip ile sıkıştırılarak kaydedilir (uzantı .json.gz).
- Başarısız çekimlerde "MISSING_" ön ekli dosya oluşturulur (yine sıkıştırılmış).
- 403/429 blokajlarında 5 dakika bekler.
"""

import requests
import json
import gzip
import time
import os
import logging
from datetime import datetime

# --- AYARLAR -------------------------------------------------
API_URL = "https://api.hypixel.net/v2/skyblock/bazaar"
API_KEY = ""                     # Varsa yaz, yoksa boş bırak (public endpoint)
DATA_DIR = "bazaar_data"         # JSON dosyalarının tutulacağı klasör
INTERVAL = 60                    # Saniye cinsinden istek aralığı
LOG_FILE = "collector.log"       # Log dosyası

# --- LOGLAMA -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Dizin kontrolü
os.makedirs(DATA_DIR, exist_ok=True)

def get_headers():
    """API anahtarı varsa header'a ekler, yoksa boş header döner."""
    headers = {
        "User-Agent": "Hypixel-Bazaar-Collector/1.0",
        "Content-Type": "application/json"
    }
    if API_KEY:
        headers["API-Key"] = API_KEY
    return headers

def fetch_bazaar():
    """Tüm bazaar verisini tek seferde çeker. Hata durumunda None döner."""
    try:
        response = requests.get(API_URL, headers=get_headers(), timeout=30)
        
        # 200 OK
        if response.status_code == 200:
            return response.json()
        
        # 403 (yasak) veya 429 (çok istek) -> ciddi blokaj
        if response.status_code in (403, 429):
            logging.error(f"KRİTİK: API blokajı! Kod: {response.status_code}. 5 dakika beklenecek.")
            time.sleep(300)   # 5 dakika ceza beklemesi
            return None
        
        # Diğer hata kodları (500, 502 vb.)
        logging.warning(f"Sunucu hatası: {response.status_code}. Bir sonraki turda dene.")
        return None
    
    except requests.exceptions.Timeout:
        logging.warning("Zaman aşımı (timeout).")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Bağlantı hatası: {e}")
        return None

def save_success(data):
    """Başarılı veriyi gzip sıkıştırmalı JSON dosyasına kaydeder."""
    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{DATA_DIR}/{timestamp_str}.json.gz"
    try:
        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(data, f)
        logging.info(f"Başarılı (sıkıştırılmış): {filename}")
        return True
    except Exception as e:
        logging.error(f"Dosya yazma hatası: {e}")
        return False

def save_gap(error_message):
    """Başarısız istek için gap dosyası oluşturur (gzip sıkıştırmalı)."""
    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{DATA_DIR}/MISSING_{timestamp_str}.json.gz"
    gap_data = {
        "error": True,
        "timestamp": int(now.timestamp()),
        "reason": error_message,
        "expected_interval": INTERVAL
    }
    try:
        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(gap_data, f)
        logging.warning(f"Gap kaydı (sıkıştırılmış): {filename} - Sebep: {error_message}")
        return True
    except Exception as e:
        logging.error(f"Gap dosyası yazılamadı: {e}")
        return False

def main():
    logging.info("Bazaar toplayıcı başladı (gzip sıkıştırmalı).")
    consecutive_errors = 0

    while True:
        start_time = time.time()

        # 1. Veriyi çek
        data = fetch_bazaar()

        if data and data.get("success"):
            consecutive_errors = 0
            save_success(data)
        else:
            consecutive_errors += 1
            error_msg = f"Veri alınamadı (ardışık hata: {consecutive_errors})"
            logging.warning(error_msg)
            save_gap(error_msg)

            # Çok fazla ardışık hata varsa uzun bekle
            if consecutive_errors > 10:
                logging.error("Ardışık 10+ hata. 10 dakika bekleniyor...")
                time.sleep(600)
                consecutive_errors = 0
                continue  # Bu bekleme sonrası hemen yeni döngüye gir

        # 2. Döngü aralığını koru
        elapsed = time.time() - start_time
        sleep_time = max(0, INTERVAL - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()