# Projekt: hc_haco2 (home-heizungscontroller)

Du bist ein erfahrener Python- und IoT-Architekt.
Ist ein größeres Projekt, bitte arbeite extrem effizient und minimiere Tokenverbrauch.

Ziel: Refactor + Stabilisierung + Docker + Dashboard 
      Python IoT Heizungs-Systems,saubere, wartbare Architektur und 
      Anwendung für Docker Deployment.

## Hardware - Geräte Übersicht
- Gasmeter: BK-G2,5 + IN-Z61 SENSOR + ESP HOME ESP32
- Gastherme: LOGAMAX PLUS GB172-14
- Warmwasserspeicher: Geminox BS 150 - EBS 1-150
- Heizkörper: 13 über 3 Geschosse

```
            GAS
             │
        Gaszähler
             │
             ▼
        ┌───────────┐
        │  Therme   │
        │ GB172-14  │
        └────┬──────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼

 HEIZKREIS       WARMWASSER
 (Radiatoren)      (Speicher)

   │                  │
   │                  ▼
   │           ┌────────────┐
   │           │  Speicher  │ <-- Kaltwasser Zulauf
   │           │   BS 150   │
   │           └────┬───────┘
   │                │
   │                ▼
   │           Warmwasser
   │
   ▼
Heizkörper (13 über 3 Stockwerke)
   │
   ▼
 Rücklauf → zurück zur Therme
```


---

# 🎯 Ziel des Systems

Das System soll:

- Gasverbrauch und Heizungsdaten erfassen (EMS-ESP32 + Gaszähler ESPHome)
- Betriebszustände der Heizung berechnen:
  - Heizen
  - Heizkörper
  - Boiler
  - Desinfektion
- Kennzahlen der Heizung erfassen und berechnen
- Verbrauchskennzahlen
- Kostenermittlung
- MQTT Daten an Broker senden (optional)
- Daten in SQLite + CSV speichern (Re-Import möglich)
- Keine Update / Recalc der SQLite falls sich Einstellungen ändern
- Events an Home Assistant per Webhook senden
- Dashboard zur Visualisierung bereitstellen

---

# 📤 Geplantes Vorgehen

1. Analyse
2. Struktur Plan
3. Refactor Schritte
4. File Mapping
5. Docker Setup
6. Dashboard Design

# ⚙️ HARTE REGELN
- kein Trial-and-Error Code
- keine parallele Backend + UI Entwicklung
- jede Phase muss einzeln lauffähig sein
- bei Unsicherheit → STOPP + Rückfrage

---

# ⚠️ Ausgangslage (IST)

- Im Order lib habe ich versucht das datenmodell und die datenbeschaffung anzulegen
- Testergebnisse sind nicht richtig

- In data/raw sind die json dateien vom EMS-ESP32 und ESP Gasmeter

- Die Heizung verwendet die Daten vom EMS-ESP32 
  Firmware: v3.8.1 (Projekt https://github.com/emsesp/EMS-ESP32).

- Daten Heizung ems-heizung.siebler.home
  "curl -v http://ems-heizung.siebler.home/api/boiler"
  Hinweis: Json Datenstruktur kann sich ändern, Mappings ?
  
- Daten Gasverbrauch ESPHOME ESP Anwendung (Gas in m3)
  curl -i http://10.1.1.246/text_sensor/gasmeterdata
  Hinweis: Json Datenstruktur kann sich ändern, Mappings ?

---

## Kennzahlen ermitteln bzw. Berechnen
   - Gerätedaten
     - Gastherme
     - Bolier Warmwasser, Desinfizierung
     - Gaszähler
   - Betriebdauer
     - Anlage gesamt
     - Boiler Betrieb
     - Heizkörper Betrieb
     - Desinfizierung Betrieb
     - Anlage gesamt Laufzeit (installiert seit) 
   - Heizbetrieb (Sommer /Winter )
   - Status Betriebsart pro Zeitraum
     - Heizen (Heizkörper)
     - Warmwasseraufbreitung
     - Desinfizierung 
   - Temperatur aktuell, letzte
     - Boiler
     - Heizkörper (Vorlauf, Rücklauf)
     - Desinfizierung
   - Verbrauch Gas/Tag
     - Gesamt
     - Verbrauch Heizkörperbetrieb (Heizen)
     - Verbrauch Warmwasseraufbereitung (Boiler)
     - Verbrauch Desinfizierung (Boiler)
   - Verbrauch Enegie/Tag
     - Gesamt
     - Verbrauch Heizkörperbetrieb (Heizen)
     - Verbrauch Warmwasseraufbereitung (Boiler)
     - Verbrauch Desinfizierung (Boiler)  
   - Kosten
     - Energie Gesamt
     - Energie Heizkörperbetrieb (Heizen)
     - Energie Warmwasseraufbereitung (Boiler)
     - Energie Desinfizierung (Boiler)
     - Gas Gesamt
     - Gas Heizkörperbetrieb (Heizen)
     - Gas Warmwasseraufbereitung (Boiler)
     - Gas Desinfizierung (Boiler)     
   - Fehlermeldung
     - Anzahl
     - Meldung mit Datum
     - Letzte  mit Datum
   - Leisungskennzahlen Gastherme
   - Außentemperatur (Verlauf)  
   
---

# 🪜 TASK 1 – Refactor + Stabilisierung

## 🎯 Ziel
Bestehendes System stabilisieren und in neue Struktur überführen, ohne lint und ruff check Fehler

---

## 🔧 Schritte (streng in Reihenfolge ausführen)

### 1. Analyse
- Hauptprobleme auflisten (max 10 Punkte)
  
---

### 2. Struktur-Refactor
- Datenklassen und Datenbeschaffung optimieren
- Fehler beheben

Ziel: zuerst Datenklassen und Datenbeschaffung verbesseren dann Berechnunglogik erstellen.

---

### 3. Logik-Konsolidierung
- keine doppelte Funktionen
- heizung und utils/lib sauber trennen

---

### 4. Config + Logging
- Keine Hardcoded Einträge
- zentrale Config in config/app_config + .env
- Preise Gas- und Strom (Energie) in costs.yaml
- Sprachdatei config/lang (z.Zeit nur für HA Discovery)
- Logging einbauen (derzeit nur print ausgaben)
  - Production:  INFO (wenig nur die wichtigsten)
  - Development: DEBUG
  - App Flow-Tracer einbauen , ein/aus mit .env Einstellung in eine Datei speichern.

---

### 5. MQTT single publish einbauen
- reconnect + retry Mechanismus
- publish nur bei validen Daten
- keine doppelten Messages
- MQTT optional (aktvi nur wenn in .env eingetragen)
  Anwendung muss weiterlaufen wenn kein MQTT Brocker vorhanden ist

---

### 6. Docker Setup
- Dockerfile (keines image)
- MQTT Broker mosquitto, sollte auch ohne MQTT laufen
- Healthcheck Dockeranwendung
- .dockerignore erstellen
- Makefile (build/run/stop ...)

---

# 🪜 TASK 2 – Dashboard (NACH Backend Stabilität)

## 🎯 Ziel
Dashboard zur Visualisierung von Status, Energie, Trends und Events.

---

## ⚠️ WICHTIG
- NGINX einer Weiterleitung muss gehen (index.html, js, css, bilder)
  location: /dashboardhaco
- Dashboard optimal anlegen.
- Einstellungen über .env
- Optional Sprache Einstellungen
- keine eigene Business-Logik im UI
- Backend darf NICHT verändert werden
- Farben Einstellung über Konfiguration (Hintergrundfarbe)
- Port frei konfigurierbar
- Für Desktop und Mobile (Handy, Tablet)
---

## 🧱 UI Struktur

### Header
- Titel
- letzter Update Timestamp
- Zeitraumfilter:
  - Monat
  - Jahr
  - frei (von-bis)

---

## 🔥 KACHELN – Betriebszustände


- Progress bar Anzeige Heizung Standby, Heizbetrieb, Boilerbetrieb, Desinfizierung  
  Zeitachse 24 h
- Modernes ralistisches Flowchart Heizungsanlage:
   Gas -> Therme -> Betrieb Warmwasser Desinfiierung, Heizkörperbetrieb

---

## ⚠️ KACHEL FEHLER

- Kachel letzter Fehlercode und Anzahl der Fehler
  - nur anzeigen wenn geändert
  - Warnstatus bei Änderung

---

## 🌡️ TEMPERATUREN Grafiken
- Heizkreis Temperatur
- Warmasser Temperatur
- Trendverlauf

---

## 💧 VERBRAUCH ⚡ ENERGIE kWh und GAS

- Gasverbrauch kWh nach Betriebsart (Heizkörper, Boiler, Desinfektion)
- Energieverbrauch nach Betriebsart (Heizkörper, Boiler, Desinfektion)
- Zusammenfassung und Trends

## ⚡ Kosten
- Heizen
- Boiler
- Desinfektion
- Gesamttrend

---

## 📊 ERWEITERTE WERTE

- Brennerlaufzeit
- Starts
- Vorlauf / Rücklauf
- Pumpenstatus
- WWK Daten
- Statuscodes
- zusätzlich wichtige für Heizung, Boiler


## 📊 Export csv für Excel, Numbers
- richtiges Dezimaltrennzeichen (,)
- Geeignet für Re-Import der Daten

---

## Home Assistant

### 🔔 EVENTS – Home Assistant Webhook

Trigger nur bei Änderungen:

- neuer Fehler
- Fehler geändert
- Betriebsmodus geändert
- System OK wiederhergestellt
- Temperaturwarnung:
  dhw.curtemp < (flowtempoffset - 5)

### HA Discovery einbauen

---


