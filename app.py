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
    # TFF'nin belirttiğiniz sayfası (Örn: Puan durumu ve fikstür sayfası)
    url = "https://www.tff.org/default.aspx?pageID=198"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    scraped_data = {
        "status": "success",
        "updated_at": int(time.time()),
        "tables": []
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Sayfadaki TÜM HTML tablolarını bul
            tables = soup.find_all('table')
            
            for index, table in enumerate(tables):
                table_rows = []
                rows = table.find_all('tr')
                
                for row in rows:
                    # Tablo içerisindeki başlık (th) ve hücre (td) verilerini al
                    cols = row.find_all(['th', 'td'])
                    cols_text = [col.text.strip() for col in cols if col.text.strip()]
                    
                    if cols_text:
                        table_rows.append(cols_text)
                
                # Eğer tabloda anlamlı veri varsa listeye ekle
                if len(table_rows) > 1:
                    scraped_data["tables"].append({
                        "table_index": index + 1,
                        "rows": table_rows
                    })
                    
    except Exception as e:
        scraped_data["status"] = "error"
        scraped_data["message"] = str(e)

    return scraped_data

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "endpoint": "/api/superlig"})

@app.route('/api/superlig', methods=['GET'])
def get_superlig():
    current_time = time.time()
    
    # 2 dakikalık ön bellek (cache) kontrolü
    if cache_data["payload"] and (current_time - cache_data["timestamp"] < CACHE_TIMEOUT):
        return jsonify(cache_data["payload"])
    
    fresh_data = fetch_superlig_data()
    cache_data["timestamp"] = current_time
    cache_data["payload"] = fresh_data
        
    return jsonify(fresh_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)