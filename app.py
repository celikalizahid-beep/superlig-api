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
    url = "https://www.tff.org/default.aspx?pageID=198"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    standings = []
    matches = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Sayfadaki tüm tabloları tarayıp Süper Lig verilerini ayıklıyoruz
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    cols_text = [col.get_text(separator=" ", strip=True).replace("\n", " ").replace("\r", "") for col in cols]
                    cols_text = [text for text in cols_text if text]
                    
                    if not cols_text:
                        continue
                    
                    # Puan Durumu Satır Algılama (Takım, Oynanan, Puan içeren sütun yapısı)
                    # Genellikle TFF tablosunda sıra, takım adı, o, g, b, m, a, y, av, p bulunur
                    if len(cols_text) >= 9 and cols_text[0].isdigit() and int(cols_text[0]) <= 20:
                        standings.append({
                            "pos": cols_text[0],
                            "team": cols_text[1],
                            "p": cols_text[2],
                            "pts": cols_text[-1] # Son sütun puandır
                        })
                        
    except Exception as e:
        print(f"Hata: {e}")

    return {
        "status": "success",
        "updated_at": int(time.time()),
        "super_lig_puan_durumu": standings
    }

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "endpoint": "/api/superlig"})

@app.route('/api/superlig', methods=['GET'])
def get_superlig():
    current_time = time.time()
    
    if cache_data["payload"] and (current_time - cache_data["timestamp"] < CACHE_TIMEOUT):
        return jsonify(cache_data["payload"])
    
    fresh_data = fetch_superlig_data()
    cache_data["timestamp"] = current_time
    cache_data["payload"] = fresh_data
        
    return jsonify(fresh_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)