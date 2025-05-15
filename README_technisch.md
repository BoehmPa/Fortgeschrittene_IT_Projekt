
# Wetter-Vergleichs-App (Flask + OpenWeather)

Ein modernes Webprojekt zur Anzeige und dem Vergleich von Wetterdaten für bis zu 3 Städte – mit dynamischem Hintergrund, Darkmode und ansprechender UI.

---

## Installation & Setup

1. **Projektordner öffnen**

2. **Abhängigkeiten installieren**  
   ```bash
   pip install -r requirements.txt
   ```
3. **Flask starten**  
   ```bash
   flask run
   ```

---

## requirements.txt

```txt
Flask
requests
```
---

##  Projektstruktur

```
├── backend.py         # Flask-Backend
├── templates/
│   └── index.html     # HTML-Frontend
├── static/
│   └── style.css      # CSS-Design
└── requirements.txt
```

---

##  backend.py

Das Backend nutzt Flask und verarbeitet sowohl GET- als auch POST-Anfragen.

### 🔹 Aufbau:
---

#### Module importieren

```python
from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
```
> #### Basis-URL der Wetter-API mit metrischen Einheiten und deutscher Sprache
```python
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
```
```python
API_KEY = "DEIN_API_KEY_HIER"
```

#### Hilfsfunktion um Unix-Zeitstempel der API in lesbares Format umzuwandeln
```python
def unix_to_time(ts):
    return datetime.fromtimestamp(ts).strftime('%H:%M')
```

#### 🔹 Route `/`
```python
@app.route("/", methods=["GET", "POST"])
def home():
```
- Bei `GET`: Seite laden
- Bei `POST`: Städte auslesen, Wetterdaten laden und weitergeben

#### 🔹 Datenverarbeitung
```python
stadt1 = request.form.get("stadt1", "")
```
- Liest User-Eingabe aus dem Formular

```python
response = requests.get(WEATHER_URL, params=params)
data = response.json()
```
- Holt Wetterdaten von OpenWeatherMap

#### 🔹 Zeit- und Wetterklassen
```python
now_unix = datetime.now().timestamp()
if now_unix < sunrise_unix:
    tageszeit = "night"
...
wetterklasse = f"{wetterlage}-{tageszeit}"
```
- Definiert, ob „clear-day“, „rain-night“ usw. → für CSS

#### 🔹 Ausgabe an HTML
```python
return render_template("index.html", wetterdaten=wetterdaten)
```
- Übergibt strukturierte Wetterdaten-Liste an die HTML-Vorlage

---

##  API-Quelle

[OpenWeatherMap API](https://openweathermap.org/current)

```http
GET http://api.openweathermap.org/data/2.5/weather?q=Berlin&appid=<API_KEY>&units=metric
```

---
