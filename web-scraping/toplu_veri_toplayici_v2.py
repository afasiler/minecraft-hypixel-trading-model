import requests
import csv
import time
import os
from datetime import datetime

# --- AYARLAR ---
API_URL = "https://api.hypixel.net/v2/skyblock/bazaar"

ITEMS = ["SHARD_GLACITE_WALKER", "SOULFLOW", "ESSENCE_CRIMSON", "CORRUPTED_NETHER_STAR", "TOXIC_ARROW_POISON", "SHARD_ZOMBIE_SOLDIER", "SHARD_GHOST", "FUMING_POTATO_BOOK", "HOT_POTATO_BOOK", "PLASMA", "ENCHANTMENT_GROWTH_6", "TITANIC_EXP_BOTTLE", "GRAND_EXP_BOTTLE", "ENCHANTED_BAKED_POTATO", "TARANTULA_CATALYST", "WITHER_BLOOD", "JUNGLE_KEY", "RITUAL_RESIDUE", "GREEN_CANDY", "PURPLE_CANDY", "RED_GIFT", "WHITE_GIFT", "GREEN_GIFT", "RECOMBOBULATOR_3000", "TARANTULA_SILK", "RUSTY_COIN"]

OUTPUT_FOLDER = "CSVs"

def fetch_bazaar_data(item_name):
    """
    Hypixel API'den veriyi çeker ve sadece hedef itemin quick_status'unu döndürür.
    """
    try:
        response = requests.get(API_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Ürünün verisine ulaşalim
            if "products" in data and item_name in data["products"]:
                return data["products"][item_name]["quick_status"]
            else:
                print(f"Hata: {item_name} API verisinde bulunamadi.")
                return None
        else:
            print(f"API Hatasi: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Bağlanti Hatasi: {e}")
        return None

def save_to_csv(data, csv_file):
    """
    Gelen veriyi CSV dosyasina ekler.
    """
    # Zaman bilgileri
    data['timestamp'] = int(time.time())  # Unix zamani (ML için)
    data['readable_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Okunabilir tarih
    
    # CSV sütun sirasi
    columns = [
        'timestamp', 'readable_date', 
        'sellPrice', 'sellVolume', 'sellMovingWeek', 'sellOrders', 
        'buyPrice', 'buyVolume', 'buyMovingWeek', 'buyOrders'
    ]
    
    # Dosyanin olup olmadiğini kontrol et
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            
            # Eğer dosya yeni oluşturuluyorsa başliklari (header) yaz
            if not file_exists:
                writer.writeheader()
            
            # İstediğimiz sütunlari çek ve yazdir
            row_to_write = {col: data.get(col) for col in columns}
            writer.writerow(row_to_write)
            
    except IOError as e:
        print(f"Dosya Yazma Hatasi: {e}")

# --- ANA DÖNGÜ ---
if __name__ == "__main__":
    print("Veri toplama başlatiliyor")
    print("Durdurmak için CTRL+C yapabilirsiniz.\n")

    while True:
        starting_time = time.time() # Başlarkenki zaman

        for item in ITEMS:
            csv_filename = os.path.join(OUTPUT_FOLDER, f"{item}_dataset.csv") 
            market_data = fetch_bazaar_data(item)
            if market_data:
                save_to_csv(market_data, csv_filename)

        finishing_time = time.time() # Bitince zaman
        duration = finishing_time - starting_time
        if duration < 60:
            time.sleep(60 - (duration)) # Bir döngüyü 60 saniyeye tamamla
        
        
        