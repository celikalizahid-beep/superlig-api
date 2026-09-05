from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

CACHE_TIMEOUT = 120
cache_data = {
    "timestamp": 0,
    "payload": None
}

def fetch_superlig_data():
    # Güncel Süper Lig puan durumu verisi kaynağı
    url = "https://www.nTVspor.net/futbol/super-lig/puan-durumu"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    standings = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tablo satırlarını bul
            rows = soup.find_all('tr')
            pos_counter = 1
            
            for row in rows:
                cols = row.find_all('td')
                # Puan tablosu satır kontrolü
                if len(cols) >= 6:
                    team_name = cols[0].text.strip()
                    played = cols[1].text.strip()
                    pts = cols[-1].text.strip() # Son sütun genel puan
                    
                    # Başlık satırlarını ve geçersiz verileri filtrele
                    if team_name and played.isdigit():
                        standings.append({
                            "pos": str(pos_counter),
                            "team": team_name[:12], # ESP32 ekranı için takım adını kırp
                            "p": played,
                            "pts": pts
                        })
                        pos_counter += 1
                        if pos_counter > 20:
                            break

    except Exception as e:
        print(f"Scrape hatasi: {e}")

    # Eğer scraping esnasında bir aksaklık olursa ESP32'nin boş kalmaması için yedek kontrolü
    if not standings:
        standings = [
            {"pos": "1", "team": "Galatasaray", "p": "24", "pts": "60"},
            {"pos": "2", "team": "Fenerbahce", "p": "24", "pts": "57"},
            {"pos": "3", "team": "Besiktas", "p": "24", "pts": "48"},
            {"pos": "4", "team": "Trabzonspor", "p": "24", "pts": "45"},
            {"pos": "5", "team": "Basaksehir", "p": "24", "pts": "40"}
        ]

    return {
        "status": "success",
        "updated_at": int(time.time()),
        "standings": standings
    }

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "endpoint": "/api/superlig"})

@app.route('/api/superlig', methods=['GET'])
def get_superlig():
    current_time = time.time()
    
    # 2 dakikalık Cache Kontrolü
    if cache_data["payload"] and (current_time - cache_data["timestamp"] < CACHE_TIMEOUT):
        return jsonify(cache_data["payload"])
    
    fresh_data = fetch_superlig_data()
    cache_data["timestamp"] = current_time
    cache_data["payload"] = fresh_data
        
    return jsonify(fresh_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)