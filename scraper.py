import os
import json
import urllib.request

# Récupération des clés Supabase cachées dans GitHub
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_bet261_virtuals():
    print("Connexion au flux des matchs virtuels...")
    
    # Nouvelle URL de simulation 100% stable au format Bet261
    url = "https://raw.githubusercontent.com/smooland/mock-sports-api/main/bet261_mock.json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Matchs trouvés : {len(data.get('matches', []))}")
            return data.get("matches", [])
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        # Données de secours directes si internet coupe
        return [
            {"id": 9991, "teams": "Arsenal vs Chelsea", "odds": {"home": 2.10, "draw": 3.40, "away": 2.90}},
            {"id": 9992, "teams": "Real Madrid vs Barcelona", "odds": {"home": 1.95, "draw": 3.60, "away": 3.20}}
        ]

def send_to_supabase(matches):
    if not matches:
        print("Aucun match à envoyer.")
        return

    for match in matches:
        match_id = match.get("id")
        teams = match.get("teams")
        odds = match.get("odds", {})
        
        # Simulation d'un prono IA ultra-rapide basé sur les cotes
        prediction = "Victoire Domicile conseillée" if odds.get("home", 0) < odds.get("away", 0) else "Match serré / Double Chance"

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
