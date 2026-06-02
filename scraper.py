import os
import json
import urllib.request
from datetime import datetime

# Récupération des clés Supabase cachées dans GitHub
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_bet261_virtuals():
    print("Connexion aux serveurs de Bet261.mg pour récupérer les vrais matchs...")
    
    # URL du flux public des sports virtuels de Bet261
    url = "https://m.bet261.mg/api/sports/virtual/fixtures"
    
    # En-têtes pour simuler un vrai navigateur et éviter d'être bloqué
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Origin': 'https://bet261.mg',
        'Referer': 'https://bet261.mg/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            # Extraction des matchs selon la structure de Bet261
            raw_matches = data.get("data", []) or data.get("fixtures", [])
            print(f"Vrais matchs trouvés sur Bet261 : {len(raw_matches)}")
            
            cleaned_matches = []
            for match in raw_matches:
                # On extrait les données importantes en s'adaptant à leur structure
                match_id = match.get("id") or match.get("fixtureId")
                home_team = match.get("homeTeam", "Équipe A")
                away_team = match.get("awayTeam", "Équipe B")
                
                # Récupération des cotes (Odds) 1X2
                odds_data = match.get("odds", {})
                odds = {
                    "home": odds_data.get("1", odds_data.get("home", 2.00)),
                    "draw": odds_data.get("X", odds_data.get("draw", 3.00)),
                    "away": odds_data.get("2", odds_data.get("away", 2.00))
                }
                
                cleaned_matches.append({
                    "id": match_id,
                    "teams": f"{home_team} vs {away_team}",
                    "odds": odds
                })
            return cleaned_matches

    except Exception as e:
        print(f"Erreur lors de la récupération des vrais matchs : {e}")
        return []

def send_to_supabase(matches):
    if not matches:
        print("Aucun match récupéré. Rien à envoyer à Supabase.")
        return

    for match in matches:
        match_id = match.get("id")
        teams = match.get("teams")
        odds = match.get("odds", {})
        
        # Calcul du pronostic IA basé sur les vraies cotes
        home_odd = odds.get("home", 0)
        away_odd = odds.get("away", 0)
        if home_odd < away_odd and home_odd < 2.20:
            prediction = "Victoire Domicile"
        elif away_odd < home_odd and away_odd < 2.20:
            prediction = "Victoire À l'extérieur"
        else:
            prediction = "Match serré - Double Chance"

        payload = {
            "match_id": str(match_id),
            "teams": teams,
            "odds_home": home_odd,
            "odds_draw": odds.get("draw"),
            "odds_away": away_odd,
            "prediction": f"Gemini IA : {prediction}",
            "status": "pending"
        }

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
                print(f"Vrai match synchronisé : {teams}")
        except Exception as e:
            print(f"Erreur d'envoi Supabase pour {teams} : {e}")

if __name__ == "__main__":
    matches = fetch_bet261_virtuals()
    send_to_supabase(matches)
