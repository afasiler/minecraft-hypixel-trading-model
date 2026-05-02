#!/usr/bin/env python3
import requests
import json
import gzip
import time
import os
import logging
import gc  # Garbage Collector - RAM yönetimi için kritik
from datetime import datetime, timezone

# --- AYARLAR -------------------------------------------------
API_URL = "https://api.hypixel.net/v2/skyblock/bazaar"
DATA_DIR = "bazaar_data"
INTERVAL = 60
LOG_FILE = "collector.log"

# --- LOGLAMA (I/O OPTİMİZE EDİLDİ) ---------------------------
# Sadece dosyaya yazar, terminal/SSH yükünü sıfırlar.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE)] 
)

os.makedirs(DATA_DIR, exist_ok=True)

def fetch_and_save():
    """Veriyi çeker ve doğrudan sıkıştırarak diske yazar."""
    try:
        response = requests.get(API_URL, timeout=20)
        if response.status_code == 200:
            data = response.json()
            
            now = datetime.now(timezone.utc)
            filename = f"{DATA_DIR}/{now.strftime('%Y-%m-%d_%H-%M-%S')}.json.gz"
            
            # compresslevel=9: Maksimum sıkıştırma (CPU yükü artar ama disk I/O azalır)
            with gzip.open(filename, "wt", encoding="utf-8", compresslevel=9) as f:
                json.dump(data, f)
            
            logging.info(f"Kaydedildi: {filename}")
            return True
        else:
            logging.warning(f"API Hatası: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Kritik Hata: {e}")
        return False

def main():
    logging.info("Bazaar V3 Hardened başladı.")
    while True:
        start_time = time.time()
        
        # 1. RAM'i zorla temizle (Headless sistemde kilitlenmeyi önler)
        gc.collect()
        
        # 2. İşlemi yap
        fetch_and_save()
        
        # 3. Döngü aralığını koru ve işlemciye nefes aldır
        elapsed = time.time() - start_time
        sleep_time = max(1, INTERVAL - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()