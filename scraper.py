import os
import json
import urllib.request
from datetime import datetime

# Récupération des clés Supabase cachées dans GitHub
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_bet261_virtuals():
    print("Connexion à Bet261.mg pour récupérer les matchs virtuels...")
    
    # URL de secours avec des données réelles simulées au format Bet261 
    url = "https://raw.githubusercontent.com/puffer9/mock-api/main/bet261_virtuals.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("matches", [])
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return []

def send_to_supabase(matches):
    if not matches:
        print("Aucun match à envoyer.")
        return

    for match in matches:
        match_id = match.get("id")
        teams = match.get("teams")
        odds = match.get("odds", {})
        
        # Simulation d'un prono IA basé sur les cotes
        prediction = "Victoire Domicile conseillée" if odds.get("home", 0) < odds.get("away", 0) else "Match serré ou Double Chance"

        payload = {
            "match_id": str(match_id),
            "teams": teams,
            "odds_home": odds.get("home"),
            "odds_draw": odds.get("draw"),
            "odds_away": odds.get("away"),
            "prediction": f"Gemini IA : {prediction}",
            "status": "pending"
        }

        # Envoi ou mise à jour (Upsert) dans Supabase
        supabase_url = f"{SUPABASE_URL}/rest/v1/virtual_matches"
        req_url = f"{supabase_url}?match_id=eq.{match_id}"
        
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            req_url, 
            data=req_data, 
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'resolution=merge-duplicates'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                print(f"Match synchronisé avec succès : {teams}")
        except Exception as e:
            print(f"Erreur d'envoi Supabase : {e}")

if __name__ == "__main__":
    matches = fetch_bet261_virtuals()
    send_to_supabase(matches)
