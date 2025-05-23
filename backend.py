from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

API_KEY = "d5184ab550c97fc5751ba70bb99170a0" # API-Key per Anmeldung erhalten, kann trotzdem verwendet werden -> nicht Gerätespezifisch
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
MAP_API_KEY = "7c3HAU4Hm6tRFxQau4FQ" # dazu da, eine englischsprachige Map aufzurufen

# Globale Variable für die Wetterdaten
weatherdata_global = []
# Hilfsfunktion: Unix-Timestamp (z.B. von Sonnenaufgang) in lesbare Uhrzeit umwandeln
def unix_to_time(timestamp, offset_seconds):
    # Wandelt Unix-Zeit + Offset in 'HH:MM' lokale Zeit um
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc) # Erstellt ein datetime-Objekt in der UTC-Zeitzone
    local_time = utc_time + timedelta(seconds=offset_seconds) # Rechnet den Zeitzonen-Offset der Stadt drauf – z.B. +3600 für MEZ oder -18000 für New York
    return local_time.strftime('%H:%M')

def unix_to_local_datetime(timestamp, offset_seconds):
    # Gibt ein datetime-Objekt in lokaler Zeit zurück (für Vergleiche)
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return utc_time + timedelta(seconds=offset_seconds)

# Startseite der App, GET zum Anzeigen, POST wenn Nutzer Städte eingegeben hat
@app.route("/", methods=["GET", "POST"])
def home():
    global weatherdata_global # auf die globale Wetterdatenliste zugreifen
    weatherdata = []  # Liste zum Sammeln der Wetterdaten

    if request.method == "POST":
        # Schleife über die 3 Eingabefelder (stadt1, stadt2, stadt3)
        for i in range(1, 4):
            stadt = request.form.get(f"stadt{i}")  # Eingabewert aus Formular holen
            if stadt:
                # Parameter für den API-Call vorbereiten
                params = {
                    "q": stadt,              # Stadtname q = Query (von OpenWeatherMap vorgeschrieben)
                    "appid": API_KEY,        # Dein API-Key
                    "units": "metric",       # °C statt Kelvin
                    "lang": "de"             # Sprache: Deutsch
                }
                # Anfrage an OpenWeatherMap senden
                response = requests.get(WEATHER_URL, params=params)
                if response.status_code == 200:
                    data = response.json()  # Antwort in JSON umwandeln -> Weiterverarbeitung

                    # lokale Uhrzeit
                    now_local = datetime.now(timezone.utc) + timedelta(seconds=data["timezone"])

                    # Lokale aktuelle Uhrzeit berechnen (für Anzeige)
                    local_time_str = now_local.strftime('%H:%M') + "Uhr"

                    # Sonnenauf- und -untergang in lokale Zeit umwandeln
                    # Diese Zeitstempel sind in UTC und müssen in die jeweilige Ortszeit der Stadt umgerechnet werden
                    sunrise_local = unix_to_local_datetime(data["sys"]["sunrise"], data["timezone"])
                    sunset_local = unix_to_local_datetime(data["sys"]["sunset"], data["timezone"])
                    
                    # Die berechneten lokalen Zeiten (datetime-Objekte) werden nun formatiert
                    # Die Uhrzeiten werden als String im Format "HH:MM" gespeichert, um sie später im Frontend anzuzeigen
                    sunrise_str = sunrise_local.strftime('%H:%M') + "Uhr"
                    sunset_str = sunset_local.strftime('%H:%M') + "Uhr"
                    # Übergangsphasen definieren
                    if now_local < sunrise_local:
                        tageszeit = "night"
                    elif sunrise_local <= now_local <= (sunrise_local + timedelta(minutes=30)): #timedelta definiert hier einen Zeitrum von 30 Minuten
                        tageszeit = "sunrise"
                    elif sunset_local <= now_local <= (sunset_local + timedelta(minutes=30)):
                        tageszeit = "sunset"
                    elif now_local > (sunset_local + timedelta(minutes=30)):
                        tageszeit = "night"
                    else:
                        tageszeit = "day"

                    # Zusammenbauen der Wetterklasse, um dynamische Hintergründe zu ermöglichen
                    wetter_translation = {
                        "clear": "Klar",
                        "clouds": "Bewölkt",
                        "rain": "Regen",
                        "snow": "schnee",
                        "thunderstorm": "Gewitter",
                        "drizzle": "Nieselregen",
                        "mist": "Nebel"
                    }
                    weatherclass_en = data["weather"][0]["main"].lower()
                    weatherclass_ger = wetter_translation.get(weatherclass_en, weatherclass_en)
                    weather_class = f"{weatherclass_en}-{tageszeit}"
                    # Daten aus JSON extrahieren und abspeichern
                    weatherdata.append({
                        "name": data["name"],                               # Stadtname
                        "icon": data["weather"][0]["icon"],                 # Wetter-Icon
                        "weather": data["weather"][0]["main"],               # z.B. "Rain"
                        "description": data["weather"][0]["description"],  # z.B. "leichter Regen"
                        "temp": data["main"]["temp"],                       # Temperatur
                        "feels_like": data["main"]["feels_like"],           # Gefühlt wie
                        "temp_min": data["main"]["temp_min"],               # Tagesminimale Temperatur
                        "temp_max": data["main"]["temp_max"],               # Tagesmaximale Temperatur
                        "humidity": data["main"]["humidity"],               # Luftfeuchtigkeit
                        "sunrise": sunrise_str,                             # Sonnenaufgang
                        "sunset": sunset_str,                               # Sonnenuntergang 
                        "messzeit": datetime.fromtimestamp(data["dt"]).strftime("%d.%m.%Y %H:%M"), # umgewandelter Messzeitpunkt der Daten
                        "weather_class": weather_class,                     # für die dynamischen Hintergründe
                        "weather_ger": weatherclass_ger,                    # Übersetzung der Wetterlage  
                        "local_time": local_time_str,                        # Ortszeit
                        "coord": {                                          # Koordinaten für Map
                            "lat": data["coord"]["lat"],
                            "lon": data["coord"]["lon"]}
                    })
                else:
                    weatherdata.append({
                        "name": stadt,
                        "error": "Keine Wetterdaten gefunden" # Wenn Stadt nicht gefunden -> Fehlermeldung
                    })
    weatherdata_global = weatherdata
    # HTML-Template anzeigen und Wetterdaten übergeben
    return render_template("index.html", weatherdata=weatherdata)

@app.route("/karte")

def map():
    if not weatherdata_global:
        return "Bitte zuerst Städte auf der Startseite eingeben.", 400

    # Sicherstellen, dass ALLE notwendigen Felder existieren
    safe_weatherdata = []
    for city in weatherdata_global:
        weather_class = city.get("weather_class", "clouds-day")  # Standardklasse bei Fehlern
        safe_city = {
            "name": city.get("name", "Unbekannt"),
            "coord": city.get("coord", {"lat": 0, "lon": 0}),
            "weather_ger": city.get("weather_ger", "Unbekannt"),
            "description": city.get("description", ""),
            "temp": city.get("temp", 0),
            "humidity": city.get("humidity", 0),
            "icon": city.get("icon", "01d"),
            "weather_class": weather_class
        }
        safe_weatherdata.append(safe_city)
    return render_template("map.html", weatherdata=safe_weatherdata, api_key=API_KEY, map_key=MAP_API_KEY)

# Starte die Anwendung, wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    app.run()
