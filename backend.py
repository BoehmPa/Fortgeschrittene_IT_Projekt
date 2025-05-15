from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = "d5184ab550c97fc5751ba70bb99170a0" # API-Key per Anmeldung erhalten, kann trotzdem verwendet werden -> nicht Gerätespezifisch
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Hilfsfunktion: Unix-Timestamp (z. B. von Sonnenaufgang) in lesbare Uhrzeit umwandeln
def unix_to_time(ts):
    """Wandelt Unix-Zeitstempel in 'HH:MM'-Format um"""
    return datetime.fromtimestamp(ts).strftime('%H:%M')

# Startseite der App, GET zum Anzeigen, POST wenn Nutzer Städte eingegeben hat
@app.route("/", methods=["GET", "POST"])
def home():
    wetterdaten = []  # Liste zum Sammeln der Wetterdaten

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

                    # Uhrzeiten für Sonnenaufgang und Sonnenuntergang herausfinden
                    now_local = datetime.now()

                    # Sonnenauf- und -untergang in lokale Zeit umwandeln
                    sunrise_local = datetime.fromtimestamp(data["sys"]["sunrise"])
                    sunset_local = datetime.fromtimestamp(data["sys"]["sunset"])


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
                    wetter_uebersetzung = {
                        "clear": "Klar",
                        "clouds": "Bewölkt",
                        "rain": "Regen",
                        "snow": "schnee",
                        "thunderstorm": "Gewitter",
                        "drizzle": "Nieselregen",
                        "mist": "Nebel"
                    }
                    wetterlage_en = data["weather"][0]["main"].lower()
                    wetterlage_de = wetter_uebersetzung.get(wetterlage_en, wetterlage_en)
                    wetterklasse = f"{wetterlage_en}-{tageszeit}"
                    # Daten aus JSON extrahieren und abspeichern
                    wetterdaten.append({
                        "name": data["name"],                               # Stadtname
                        "icon": data["weather"][0]["icon"],                 # Wetter-Icon
                        "wetter": data["weather"][0]["main"],               # z.B. "Rain"
                        "beschreibung": data["weather"][0]["description"],  # z.B. "leichter Regen"
                        "temp": data["main"]["temp"],                       # Temperatur
                        "feels_like": data["main"]["feels_like"],           # Gefühlt wie
                        "temp_min": data["main"]["temp_min"],               # Tagesminimale Temperatur
                        "temp_max": data["main"]["temp_max"],               # Tagesmaximale Temperatur
                        "humidity": data["main"]["humidity"],               # Luftfeuchtigkeit
                        "sunrise": unix_to_time(data["sys"]["sunrise"]),    # Sonnenaufgang 
                        "sunset": unix_to_time(data["sys"]["sunset"]),      # Sonnenuntergang 
                        "messzeit": datetime.fromtimestamp(data["dt"]).strftime("%d.%m.%Y %H:%M"), # umgewandelter Messzeitpunkt der Daten
                        "klasse": wetterklasse,                             # für die dynamischen Hintergründe
                        "wetter_de": wetterlage_de                          # Übersetzung der Wetterlage  

                    })
                else:
                    wetterdaten.append({
                        "name": stadt,
                        "fehler": "Keine Wetterdaten gefunden" # Wenn Stadt nicht gefunden -> Fehlermeldung
                    })

    # HTML-Template anzeigen und Wetterdaten übergeben
    return render_template("index.html", wetterdaten=wetterdaten)

# Starte die Anwendung, wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    app.run(debug=True)
