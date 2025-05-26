from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv 

app = Flask(__name__)

load_dotenv() # laden der .env-Datei

API_KEY = os.getenv("API_KEY")
MAP_API_KEY = os.getenv("MAP_API_KEY")
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"



weatherdata_global = []  # globale Variable für die Wetterdaten


# ================================
# HILFSFUNKTIONEN
# ================================

# Definiert einen benutzerdefinierten Jinja2-Template-Filter namens 'datetimeformat'
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%A, %d.%m.'):
    # Überprüft, ob der übergebene Wert nur ein Datum im Format 'YYYY-MM-DD' ist (also genau 10 Zeichen)
    if len(value) == 10:  
        # Wandelt den String in ein datetime-Objekt um
        dt = datetime.strptime(value, '%Y-%m-%d')
    else:
        # Falls zusätzlich eine Uhrzeit enthalten ist, wird das erweiterte Format verwendet
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    
    # Formatiert das datetime-Objekt in das gewünschte Ausgabeformat (z. B. "Montag, 20.05.")
    return dt.strftime(format)

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

# Funktion zur Abfrage und Aufbereitung der Wettervorhersage für eine bestimmte Stadt
def get_forecast(cityname):
    # Parameter für die API-Anfrage
    params = {
        "q": cityname,         # Stadtname,
        "appid": API_KEY,      # API-Schlüssel für OpenWeatherMap
        "units": "metric",     # Temperatur in Celsius
        "lang": "de"           # Sprache der Wetterbeschreibung auf Deutsch
    }
    
    # Anfrage an die OpenWeatherMap-Vorhersage-API senden
    response = requests.get(FORECAST_URL, params=params)

    # Wenn die Anfrage erfolgreich war (HTTP 200 OK)
    if response.status_code == 200:
        raw_data = response.json()  # Antwortdaten als JSON laden
        forecasts = []              # Liste für strukturierte Vorhersagedaten

        # Iteration über alle Einträge in der 5-Tage-Vorhersage (je 3 Stunden ein Eintrag)
        for entry in raw_data["list"]:
            forecasts.append({
                "timestamp": entry["dt_txt"],                  # Zeitstempel (z. B. "2025-05-24 12:00:00")
                "temp": entry["main"]["temp"],                # Temperatur in °C
                "description": entry["weather"][0]["description"],  # Wetterbeschreibung (z. B. "leichter Regen")
                "icon": entry["weather"][0]["icon"],          # Icon-Code zur Anzeige eines Wetterbildes
                "humidity": entry["main"]["humidity"],        # Luftfeuchtigkeit in %
                "wind": entry["wind"]["speed"]                # Windgeschwindigkeit in m/s
            })

        # Rückgabe eines Dictionarys mit dem Stadtnamen und der Vorhersage
        return {
            "city": raw_data["city"]["name"],  # Bestätigter Stadtname von der API
            "forecasts": forecasts             # Liste mit Wettervorhersagen
        }
    else:
        # Fehlerfall: Rückgabe einer leeren Vorhersage mit Fehlermeldung
        return {
            "city": cityname,                  # Angefragter Stadtname (auch wenn ungültig)
            "forecasts": [],                   # Leere Vorhersage
            "error": "Vorhersage nicht verfügbar"  # Fehlermeldung
        }



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
                response = requests.get(WEATHER_URL, params=params) # gibt ein Respone OBJEKT zurück keine JSON
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
                        "weather": data["weather"][0]["main"],              # z.B. "Rain"
                        "description": data["weather"][0]["description"],   # z.B. "leichter Regen"
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
                        "local_time": local_time_str,                       # Ortszeit
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

@app.route("/vorhersage")
def forecast():
    if not weatherdata_global:
        return "Bitte zuerst Städte auf der Startseite eingeben.", 400
    
    forecastdata = []
    for city in weatherdata_global:
        if not city.get("error"):
            forecastdata.append(get_forecast(city["name"]))

    return render_template("forecast.html", forecastdata=forecastdata)


# Starte die Anwendung, wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    app.run()
