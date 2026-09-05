from flask import Flask, jsonify
import requests
import time
import os

app = Flask(__name__)

# Dakikalık istek sınırını korumak için 5 dakikalık önbellek
CACHE_TIMEOUT = 300 
cache_data = {
    "timestamp": 0,
    "payload": None
}

# football-data.org API anahtarınız
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "62f3142b91304778885951b5c01dec08")

def fetch_superlig_data():
    standings = []
    upcoming_matches = []
    
    headers = {
        'X-Auth-Token': API_KEY
    }
    
    try:
        # 1. Süper Lig Puan Durumu Çekme (Kod: TUR)
        standings_url = "https://api.football-data.org/v4/competitions/TUR/standings"
        response = requests.get(standings_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            table = data.get("standings", [])[0].get("table", [])
            
            for entry in table:
                pos = str(entry.get("position", 0))
                team_name = entry.get("team", {}).get("shortName", entry.get("team", {}).get("name", "Takım"))
                played = str(entry.get("playedGames", 0))
                pts = str(entry.get("points", 0))
                
                standings.append({
                    "pos": pos,
                    "team": team_name,
                    "p": played,
                    "pts": pts
                })
        
        # 2. Gelecek Maçları Çekme
        matches_url = "https://api.football-data.org/v4/competitions/TUR/matches?status=SCHEDULED"
        matches_resp = requests.get(matches_url, headers=headers, timeout=10)
        
        if matches_resp.status_code == 200:
            matches_data = matches_resp.json()
            matches = matches_data.get("matches", [])
            
            for match in matches[:5]: # Sadece ilk 5 gelecek maç
                home_team = match.get("homeTeam", {}).get("shortName", "Ev Sahibi")
                away_team = match.get("awayTeam", {}).get("shortName", "Deplasman")
                
                upcoming_matches.append({
                    "home": home_team,
                    "away": away_team,
                    "status": "Oynanacak"
                })
                
    except Exception as e:
        print(f"API Veri Çekme Hatası: {e}")

    # Yedek liste kontrolü (API'den veri çekilemezse sistemin çökmemesi için)
    if not standings:
        standings = [
            {"pos": "1", "team": "Galatasaray", "p": "4", "pts": "12"},
            {"pos": "2", "team": "Fenerbahce", "p": "4", "pts": "10"},
            {"pos": "3", "team": "Besiktas", "p": "4", "pts": "9"}
        ]
        
    if not upcoming_matches:
        upcoming_matches = [
            {"home": "Galatasaray", "away": "Fenerbahce", "status": "Oynanacak"},
            {"home": "Besiktas", "away": "Trabzonspor", "status": "Oynanacak"}
        ]

    return {
        "status": "success",
        "updated_at": int(time.time()),
        "super_lig_puan_durumu": standings,
        "gelecek_maclar": upcoming_matches
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