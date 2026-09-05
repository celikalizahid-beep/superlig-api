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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        standings = []
        table = soup.find('table', {'class': 'tff-table'}) or soup.find('table')
        
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows[:20]:
                cols = row.find_all('td')
                if len(cols) >= 8:
                    pos = cols[0].text.strip()
                    team = cols[1].text.strip()
                    played = cols[2].text.strip()
                    pts = cols[8].text.strip() if len(cols) > 8 else cols[-1].text.strip()
                    
                    standings.append({
                        "pos": pos,
                        "team": team,
                        "p": played,
                        "pts": pts
                    })

        return {
            "status": "success",
            "updated_at": int(time.time()),
            "standings": standings
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "standings": []
        }

# Ana Sayfa Kontrolü (Artık ana adrese girince Not Found demeyecek)
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Super Lig API Servisi Calisiyor",
        "endpoint": "/api/superlig"
    })

# ESP32'nin Veri Çekeceği Adres
@app.route('/api/superlig', methods=['GET'])
def get_superlig():
    current_time = time.time()
    
    if cache_data["payload"] and (current_time - cache_data["timestamp"] < CACHE_TIMEOUT):
        return jsonify(cache_data["payload"])
    
    fresh_data = fetch_superlig_data()
    if fresh_data["status"] == "success":
        cache_data["timestamp"] = current_time
        cache_data["payload"] = fresh_data
        
    return jsonify(fresh_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)