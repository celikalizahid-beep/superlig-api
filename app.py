from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# 2 dakikalık (120 saniye) ön bellek (cache)
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

@app.route('/api/superlig', methods=['GET'])
def get_superlig():
    current_time = time.time()
    
    # Süre dolmadıysa ön bellekteki veriyi ver
    if cache_data["payload"] and (current_time - cache_data["timestamp"] < CACHE_TIMEOUT):
        return jsonify(cache_data["payload"])
    
    # Süre dolduysa sıfırdan yeni veri çek
    fresh_data = fetch_superlig_data()
    if fresh_data["status"] == "success":
        cache_data["timestamp"] = current_time
        cache_data["payload"] = fresh_data
        
    return jsonify(fresh_data)

@app.route('/')
def home():
    return "Süper Lig ESP32 API Servisi Çalışıyor!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)