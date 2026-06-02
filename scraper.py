import os
import json
import time
import urllib.request
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_with_browser():
    heure_madagascar = datetime.utcnow() + timedelta(hours=3)
    heure_locale = heure_madagascar.strftime("%H:%M")
    print(f"[{heure_locale}] Ouverture de Chrome virtuel (Contournement Cloudflare)...")
    
    url = "https://bet261.mg/virtual/category/instant-league/8035/matches"
    vrais_matchs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        def handle_response(response):
            nonlocal vrais_matchs
            if "fixtures" in response.url or "subcategories/8035" in response.url:
                try:
                    if response.status == 200:
                        data = response.json()
                        raw_fixtures = data.get("data", []) or data.get("fixtures", []) or data
                        
                        for match in raw_fixtures:
                            match_id = match.get("id") or match.get("fixtureId")
                            home = match.get("homeTeam", {}).get("name") if isinstance(match.get("homeTeam"), dict) else match.get("homeTeam")
                            away = match.get("awayTeam", {}).get("name") if isinstance(match.get("awayTeam"), dict) else match.get("awayTeam")
                            
                            if home and away:
                                odds_list = match.get("odds", []) or []
                                odds = {"home": 2.0, "draw": 3.0, "away": 2.0}
                                for market in odds_list:
                                    if any(x in market.get("name", "") for x in ["1X2", "Match Result"]):
                                        for outcome in market.get("outcomes", []):
                                            n = str(outcome.get("name", ""))
                                            if n == "1" or "home" in n.lower(): odds["home"] = float(outcome.get("value"))
                                            elif n.lower() == "x" or "draw" in n.lower(): odds["draw"] = float(outcome.get("value"))
                                            elif n == "2" or "away" in n.lower(): odds["away"] = float(outcome.get("value"))
                                
                                vrais_matchs.append({
                                    "id": match_id,
                                    "teams": f"{home} vs {away}",
                                    "odds": odds,
                                    "heure": heure_locale
                                })
                except Exception:
                    pass

        page.on("response", handle_response)
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(7)
        except Exception as e:
            print(f"Erreur de navigation : {e}")
        finally:
            browser.close()
            
    return vrais_matchs, heure_locale

def send_to_supabase(matches):
    if not matches:
        print("Aucun match réel intercepté à cette minute.")
        return

    seen = set()
    unique_matches = []
    for m in matches:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique_matches.append(m)

    for match in unique_matches:
        match_id = match.get("id")
        teams = match.get("teams")
        odds = match.get("odds", {})
        heure_match = match.get("heure")
        
        prediction = "Victoire Domicile" if odds["home"] < odds["away"] else "Match serré / Double Chance"

        payload = {
            "match_id": str(match_id),
            "teams": teams,
            "odds_home": odds["home"],
            "odds_draw": odds["draw"],
            "odds_away": odds["away"],
            "prediction": f"Gemini IA : {prediction}",
            "status": f"En cours ({heure_match})"
        }

        supabase_url = f"{SUPABASE_URL}/rest/v1/virtual_matches"
        req_url = f"{supabase_url}?match_id=eq.{match_id}"
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            req_url, 
            data=req_data, 
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as _:
                print(f"Vrai match enregistré : {teams}")
        except Exception:
            pass

def clean_old_matches():
    """Supprime les matchs terminés ou en cours qui ont été créés il y a plus de 5 minutes"""
    print("Nettoyage des anciens matchs (plus de 5 minutes)...")
    
    # 1. Calculer l'heure limite (Maintenant - 5 minutes) à Madagascar
    heure_madagascar = datetime.utcnow() + timedelta(hours=3)
    heure_limite = heure_madagascar - timedelta(minutes=5)
    
    # On va lister les 10 dernières minutes à supprimer pour être sûr de ne rien rater
    minutes_a_supprimer = []
    for i in range(5, 20): # Supprime tout ce qui a entre 5 et 20 minutes d'ancienneté
        minutes_a_supprimer.append((heure_madagascar - timedelta(minutes=i)).strftime("%H:%M"))

    for heure_cible in minutes_a_supprimer:
        # Ordre de suppression basé sur la mention de l'heure dans la colonne 'status'
        # Exemple : Supprime si le statut contient '(18:05)'
        status_recherche = f"%({heure_cible})%"
        
        # Encodage de l'URL pour Supabase
        url_encoded = urllib.parse.quote(status_recherche)
        delete_url = f"{SUPABASE_URL}/rest/v1/virtual_matches?status=like.{url_encoded}"
        
        req = urllib.request.Request(
            delete_url,
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}'
            },
            method='DELETE'
        )
        try:
            with urllib.request.urlopen(req) as _:
                pass
        except Exception as e:
            print(f"Erreur lors du nettoyage pour l'heure {heure_cible} : {e}")
            
    print("Nettoyage terminé. La base de données est propre !")

if __name__ == "__main__":
    # Étape 1 : Récupérer et envoyer les nouveaux matchs
    matches, heure = fetch_with_browser()
    send_to_supabase(matches)
    
    # Étape 2 : Supprimer automatiquement les matchs vieux de plus de 5 minutes
    clean_old_matches()
