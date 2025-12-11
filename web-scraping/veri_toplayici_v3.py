import requests
import csv
import time
import os
import logging
from datetime import datetime

# --- AYARLAR ---
API_URL = "https://api.hypixel.net/v2/skyblock/bazaar"
API_KEY = ""  # Varsa buraya yaz, yoksa boş kalsın (Public API key'siz de çalışır ama limit düşüktür)

# Hedef Eşyalar
ITEMS = [
    "SHARD_GLACITE_WALKER", "SOULFLOW", "ESSENCE_CRIMSON", "CORRUPTED_NETHER_STAR", 
    "TOXIC_ARROW_POISON", "SHARD_ZOMBIE_SOLDIER", "SHARD_GHOST", "FUMING_POTATO_BOOK", 
    "HOT_POTATO_BOOK", "PLASMA", "ENCHANTMENT_GROWTH_6", "TITANIC_EXP_BOTTLE", 
    "GRAND_EXP_BOTTLE", "ENCHANTED_BAKED_POTATO", "TARANTULA_CATALYST", "WITHER_BLOOD", 
    "JUNGLE_KEY", "RITUAL_RESIDUE", "GREEN_CANDY", "PURPLE_CANDY", "RED_GIFT", 
    "WHITE_GIFT", "GREEN_GIFT", "RECOMBOBULATOR_3000", "TARANTULA_SILK", "RUSTY_COIN"
]

OUTPUT_FOLDER = "CSVs"
LOG_FILE = "system_status.log"

# --- LOGLAMA AYARLARI ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_headers():
    headers = {
        "User-Agent": "Hypixel-Data-Collector/2.0 (Student Project)",
        "Content-Type": "application/json"
    }
    if API_KEY:
        headers["API-Key"] = API_KEY
    return headers

def fetch_all_bazaar_data():
    """
    Tüm Bazaar verisini TEK SEFERDE çeker.
    """
    try:
        response = requests.get(API_URL, headers=get_headers(), timeout=15)
        
        # 1. BAŞARILI DURUM (200 OK)
        if response.status_code == 200:
            return response.json()
        
        # 2. TEHLİKELİ DURUMLAR (429: Çok İstek, 403: Yasaklı)
        elif response.status_code in [403, 429]:
            logging.error(f"KRİTİK HATA: API Ban/Limit Engeli (Kod: {response.status_code}). 5 dakika soğumaya alınıyor.")
            time.sleep(300) # 5 dakika ceza beklemesi
            return None
            
        # 3. SUNUCU HATALARI (500, 502, 503)
        else:
            logging.warning(f"Sunucu Hatası: {response.status_code}. Bir sonraki turda tekrar denenecek.")
            return None

    except requests.exceptions.Timeout:
        logging.warning("Zaman aşımı (Timeout). İnternet yavaş.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Bağlantı koptu: {e}")
        return None

def save_item_data(product_data, item_name):
    """
    Çekilen veriyi parse edip kaydeder.
    """
    if item_name not in product_data:
        # Bazı itemler o an pazarda olmayabilir, log basıp geçelim
        return

    quick_status = product_data[item_name]["quick_status"]
    
    # Zaman damgaları
    timestamp = int(time.time())
    readable_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    csv_file = os.path.join(OUTPUT_FOLDER, f"{item_name}_dataset.csv")
    
    # Sütunlar
    columns = [
        'timestamp', 'readable_date', 
        'sellPrice', 'sellVolume', 'sellMovingWeek', 'sellOrders', 
        'buyPrice', 'buyVolume', 'buyMovingWeek', 'buyOrders'
    ]

    # Veriyi hazırla
    row_data = {
        'timestamp': timestamp,
        'readable_date': readable_date,
        'sellPrice': quick_status.get('sellPrice'),
        'sellVolume': quick_status.get('sellVolume'),
        'sellMovingWeek': quick_status.get('sellMovingWeek'),
        'sellOrders': quick_status.get('sellOrders'),
        'buyPrice': quick_status.get('buyPrice'),
        'buyVolume': quick_status.get('buyVolume'),
        'buyMovingWeek': quick_status.get('buyMovingWeek'),
        'buyOrders': quick_status.get('buyOrders')
    }

    # Dosyaya yaz (Append modu)
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
    except IOError as e:
        logging.error(f"Dosya yazma hatası ({item_name}): {e}")

# --- ANA MOTOR ---
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    logging.info(f"Toplayıcı Başlatıldı. Hedef: {len(ITEMS)} eşya.")
    
    consecutive_errors = 0 # Arka arkaya hata sayacı

    while True:
        start_time = time.time()
        
        # 1. Veriyi Çek (TEK İSTEK)
        data = fetch_all_bazaar_data()
        
        if data and "products" in data:
            consecutive_errors = 0 # Başarılıysa sayacı sıfırla
            products = data["products"]
            
            # 2. İtemleri İşle
            for item in ITEMS:
                save_item_data(products, item)
                
            logging.info("Veri seti güncellendi.")
            
        else:
            consecutive_errors += 1
            logging.warning(f"Veri alınamadı. Hata serisi: {consecutive_errors}")
            
            # Eğer 10 kereden fazla üst üste hata alırsan uzun bekle
            if consecutive_errors > 10:
                logging.error("Sistem çok fazla hata aldı. 10 dakika uyku modu.")
                time.sleep(600)
                consecutive_errors = 0

        # 3. Döngü Zamanlaması (Negatif sayı hatasını engelle)
        elapsed = time.time() - start_time
        sleep_time = max(0, 60 - elapsed) # Asla negatif olamaz
        
        time.sleep(sleep_time)