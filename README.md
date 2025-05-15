
#  Wetter-Vergleichs-App (Flask + OpenWeather)

Ein modernes Webprojekt zur Anzeige und dem Vergleich von Wetterdaten für bis zu 3 Städte – mit dynamischem Hintergrund, Darkmode und ansprechender UI.

---

##  backend.py (Flask-Anwendung)

### 🔹 Funktion: `/`
- Holt bis zu 3 Städte über Form-POST
- Ruft pro Stadt die OpenWeatherMap-API auf
- Extrahiert: Temperatur, Wetter, Icon, Min/Max, Feuchtigkeit, Sonnenauf-/untergang, etc.
- Rechnet Tageszeit (`sunrise`, `sunset`) in lokale Zeit um
- Setzt dynamische Klasse z. B. `rain-night` oder `clear-sunset`
- Gibt alles an `index.html` weiter via `render_template`

---

##  index.html

###  Aufbau
- **Header** mit Titel & Untertitel
- **Formular** für 1–3 Städte
- **Button für Darkmode (per JS)**
- **Ausgabe in `.wetter-box`-Karten**
- **Jinja2-Template** (`{{ }}` & `{% %}`) für dynamischen Inhalt

### 🔹 Besonderheiten
- Icons via OpenWeather (`img src=...`)
- Ausgabe von:
  - Temperatur, gefühlt
  - Min/Max
  - Humidity
  - Sonnenauf-/untergang
  - Zeitstempel der Messung
- Fehlerbehandlung pro Stadt (wenn API-Fehler)

---

## style.css

###  Grundstruktur

- `.wetter-box` -> zentrale Karten-Logik (Größe, Shadow, Padding, Hover)
- `.wetter-container` -> Flexbox-Raster
- `.suchformular`, `.stadt-suche` ->Form-Layout
- `.page-header` -> Header-Design mit Farbverlauf

###  Dynamische Klassen

Wetter-Karten passen sich je nach Wetter & Tageszeit an:

```css
.wetter-box.clear-night { background: linear-gradient(...); color: white; }
.wetter-box.rain-day    { background: linear-gradient(...); }
```

###  Darkmode

- Toggle per Button (`onclick="toggleDarkmode()"`)
- Speicherung via `localStorage`
- Klasse `body.darkmode` schaltet Farbschema um

---

##  Erweiterbare Features

- °C/°F-Umschalter
- Zufällige Stadt
- Kleidungsempfehlung
- Temperaturverlauf mit Chart.js
- Favoriten speichern

---

