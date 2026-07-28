---
title: "🔥 Intelligenter IoT-Heizungscontroller für Buderus Logamax"
date: 2026-07-01T13:45:00
description: "Erfassung, Berechnung und Visualisierung von Heizungsdaten einer Buderus LOGAMAX PLUS GB172-14 Gasheizung via EMS-ESP32 und ESPHome."
type: "post"
draft: false
image: "posts/smarthome-heizungscontroller/heizung.png"
author: "Peter Siebler"
snap_gallery: true
gallery: true
categories:
  - "Smarthome"
tags: ["docker", "python", "esphome", "mqtt", "homeassistant", "dashboard"]
---

[![Github Project](https://img.shields.io/badge/Project-GitHub-yellow.svg)](https://github.com/zibous/hc_heat)
[![Support author](https://img.shields.io/badge/buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoff.ee/zibous)
[![License](https://img.shields.io/badge/license-Open%20Source-green.svg)](https://opensource.org)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)


## Die Gasheizung im Smart Home unter Kontrolle

Klassische Gasthermen arbeiten oft als Blackbox im Keller. Mit **hc_haco2** zieht volle Transparenz in das Heizsystem ein. Die maßgeschneiderte Python-IoT-Anwendung aggregiert Live-Werte der Therme, berechnet Verbräuche sowie laufende Kosten in Echtzeit und stellt die Daten plattformübergreifend zur Verfügung.

<!--more-->

[![](https://shields.io)](https://github.com)

## Das Hardware-Setup

Das Projekt überwacht und steuert ein mehrstöckiges Heizsystem mit folgender Hardware-Basis:

- **Gastherme**: Buderus LOGAMAX PLUS GB172-14 (14 kW Leistung)
- **Warmwasserspeicher**: Geminox BS 150
- **Bus-Schnittstelle**: EMS-ESP32 Gateway (Firmware v3.8.1) zum Auslesen des internen EMS-Bus
- **Gaszähler**: BK-G2,5 Balgengaszähler, digitalisiert mit einem IN-Z61 Impulsgeber-Sensor und einem ESPHome-basierten ESP32
- **Heizkörper**: 13 smarte Heizkörper-Aktoren verteilt über 3 Geschosse

---

## 🏗️ App Flow & Architektur

Die Kernanwendung (`app.py`) lässt sich flexibel im Produktivbetrieb, für Testläufe (`--simulate`) oder zur einmaligen Abfrage (`--once`) starten. Die zentrale Logik übernimmt der `HeatingController`:

```text
┌─────────────────────────────────────────────────────────┐
│                      app.py                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ --once   │  │ --simulate   │  │ Produktivbetrieb  │  │
│  │ (einmal) │  │ (Testdaten)  │  │ (Hauptschleife)   │  │
│  └──────────┘  └──────────────┘  └─────────┬─────────┘  │
└────────────────────────────────────────────┬────────────┘
                                             │
                    ┌────────────────────────┐
                    │   HeatingController    │
                    │   (controller.py)      │
                    └───────────┬────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
   ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
   │ Daten holen  │   │  Berechnen      │   │  Ausgeben    │
   └──────┬───────┘   └────────┬────────┘   └─────┬────────┘
          │                    │                  │
    ┌─────┴──────┐      ┌──────┴─────┐      ┌─────┴──────┐
    │ EMS-ESP32  │      │ Runtime    │      │ Dashboard  │
    │ /api/boiler│      │ Calc       │      │ :5028      │
    ├────────────┤      ├────────────┤      ├────────────┤
    │ EMS-ESP32  │      │ Consumption│      │ SQLite DB  │
    │ /api/therm.│      │ Calc       │      ├────────────┤
    ├────────────┤      ├────────────┤      │ MQTT       │
    │ ESPHome    │      │ Cost Calc  │      │ (optional) │
    └────────────┘      │ Error Log  │      ├────────────┤
                        └────────────┘      │ Webhooks   │
                                            │ (optional) │
                                            ├────────────┤
                                            │ CSV Export │
                                            └────────────┘
```

---

## Der Hauptzyklus (Intervall: alle 60 Sekunden)

Sobald die Anwendung im Produktivmodus läuft, arbeitet sie minütlich folgende Schritte vollautomatisch ab:

1. **REST-API Abfrage (Therme)**: `HTTP GET /api/boiler` holt Daten zu Boiler, Systemzustand, Heizkreis und Warmwasser (DHW).
2. **REST-API Abfrage (Regelung)**: `HTTP GET /api/thermostat` liest den Zustand des Heizkreises 1 (HC1) und der Warmwasser-Komponente (WWK).
3. **Gaszähler-Polling**: `HTTP GET /text_sensor/gas` holt den aktuellen Zählerstand vom ESPHome-Sensor (optimiert mit TTL-Logik nur bei aktivem Brennerbetrieb).
4. **Modus-Erkennung**: Bestimmung des aktuellen Betriebszustands (*Standby / Heizung / Warmwasser / Desinfektion*).
5. **Datenhaltung**: Persistierung aller erfassten Telemetriedaten in der lokalen SQLite-Datenbank (`data/heating.db`).
6. **Verbrauchs-Analyse**: Berechnung des Gasverbrauchs aufgeteilt nach aktuellen Perioden (aktuelle Phase, Heute, kumulierter Gesamtwert).
7. **Finanz-Kalkulation**: Echtzeit-Kostenberechnung auf Basis der in der `costs.yaml` hinterlegten Gastarife.
8. **Fehler-Monitoring**: Abgleich von Kessel- und Thermostatmeldungen inklusive automatischer Übersetzung in verständlichen Klartext.
9. **Home Assistant Webhooks**: Sofortige Event-Übermittlung an Home Assistant bei relevanten Statusänderungen.
10. **MQTT-Publishing**: Optionale Datenübergabe an den MQTT-Broker inklusive integriertem Auto-Reconnect bei Verbindungsverlust.
11. **Live-Dashboard**: Aktualisierung des internen Daten-Caches zur verzögerungsfreien Darstellung im Web-Interface auf Port `5028`.

<hr style="margin-bottom: 4rem">

## 🖥️ Dashboard – Alles auf einen Blick

Das integrierte Web-Dashboard (Port 5028) ist als Single-Page Application aufgebaut und bietet sieben Hauptbereiche:

1. **Status-Leiste** – Aktueller Modus, Brenner, Pumpe, Tageswerte (Energie/Gas/Kosten)
2. **Heizungsanlage** – Flowchart: Gas → Therme → Heizkörper / Warmwasser / Desinfektion
3. **Temperaturen** – Vorlauf, Warmwasser, Außen mit Trend-Pfeilen (▲▼●)
4. **Temperaturverlauf** – 14-Tage Linien-Chart (Chart.js)
5. **Heizkurve** – Scatter-Plot: Außentemperatur → Vorlauf (nur Heizbetrieb)
6. **Energie & Kosten** – Perioden-Tabs (Heute/7T/Monat/Jahr/Zeitraum), Balken-Chart + CSV-Export
7. **Erweiterte Werte** – Fehlercodes, Kessel-Details, Warmwasser, Gaszähler, Thermostat

### Dashboard-Features
- Dark/Light Theme (gespeichert in localStorage)
- Auto-Refresh im konfigurierbaren Intervall
- CSV-Export (Semikolon, deutsches Dezimalkomma, UTF-8 BOM)
- Responsive Layout (Desktop + Mobile)
- Perioden-Auswahl wird über Sessions hinweg gespeichert

---

## 🔔 Home Assistant Webhooks

Die App sendet Events bei relevanten Änderungen direkt an Home Assistant:

| Event | Auslöser |
|-------|----------|
| `mode_changed` | Betriebsmodus gewechselt (Standby → Heizung etc.) |
| `error_boiler` | Neuer Kessel-Fehlercode (mit deutschem Klartext) |
| `error_thermostat` | Neuer Thermostat-Fehlercode |
| `temp_warning` | Warmwasser-Temperatur unter Schwellwert |
| `system_ok` | Temperatur wieder im Normalbereich |
| `mqtt_unavailable` | MQTT nach 30 Min aufgegeben |

Damit lassen sich Automationen bauen: Push bei Fehlercode, Warnung bei kaltem Warmwasser, Statistik bei Moduswechsel.

---

## ⛽ Gaszähler-Steuerung (Smart Polling)

Der ESPHome ESP32 am Gaszähler wird **nur abgefragt, wenn nötig**:

- Brenner aktiv → Gaszähler wird gelesen
- Brenner aus seit < 30 Sekunden (TTL) → noch lesen (Nachzügler)
- Brenner aus seit > 30 Sekunden → kein Polling

Das schont den ESP32 (stabiles WLAN) und verhindert unnötige HTTP-Requests. Die TTL-Logik stellt sicher, dass der letzte Gasverbrauch nach Brenner-Stopp noch erfasst wird.

---

## 🔧 YAML-basiertes Field-Mapping

Die EMS-ESP Firmware ändert gelegentlich ihre JSON-Key-Namen bei Updates. Statt den Python-Code anzupassen, werden alle API-Keys in `config/field_mappings.yaml` definiert:

```yaml
boiler:
  curFlowTemp: flow_temperature
  retTemp: return_temperature
  boilTemp: boiler_temperature
  # ...
```

Bei Firmware-Update nur die YAML anpassen – kein Deployment nötig, kein Python-Code betroffen.

---

## 📁 History CSV – Wöchentliche Langzeit-Archive

Zusätzlich zur SQLite-DB werden wöchentliche CSV-Dateien geschrieben:

- **Format**: Semikolon-getrennt, 16 Spalten, eine Zeile pro Minute
- **Dateinamen**: `2026-W28.csv`
- **Retention**: Ältere als 8 Wochen werden gelöscht (konfigurierbar)
- **Export**: Bestehende DB-Daten können nachträglich als CSV exportiert werden

Ideal für externe Analyse (Excel, Grafana) oder als zusätzliches Backup.

---

## 💾 Datenbank & Performance

- **SQLite** in `data/heating.db` – eine Zeile pro Zyklus (60s)
- **~525.000 Zeilen/Jahr** (~50 MB)
- **Automatisches Backup** beim Start (`.db.bak`)
- **Cleanup**: Daten älter als 2 Jahre werden automatisch gelöscht
- **Separate Simulate-DB** für Tests (`heating_sim.db`)

<hr style="margin-bottom: 4rem">

### Anlagen-Dashboard & Verbrauchskurven
{{< gallery >}}
  {{< image-dir >}}
{{< /gallery >}}

<hr style="margin-bottom: 4rem">

{{< notice tip >}}
  &raquo; **Kosten-Tipp:** Passe die Verbrauchspreise in der `costs.yaml` bei Tarifänderungen sofort an, um die finanzielle Hochrechnung im Dashboard exakt zu halten.<br>
  &raquo; **Brenner-Schonung:** Überwache die Taktung des Brenners im Live-Dashboard. Zu häufiges Anspringen deutet auf eine fehlerhafte Hysterese oder falsche Einstellungen der Heizkurve hin.<br>
  &raquo; **Field-Mapping:** Bei EMS-ESP Firmware-Update die `config/field_mappings.yaml` prüfen – API-Keys ändern sich gelegentlich, der Python-Code bleibt unberührt.<br>
  &raquo; **Fehlercodes:** Buderus-spezifische Fehlercodes werden automatisch in deutschen Klartext übersetzt (`errorcodes_de.yaml`). Neue Codes einfach ergänzen.<br>
  &raquo; **History-Export:** Mit `python3 scripts/export_history.py --days 7` die letzten 7 Tage als CSV exportieren – inklusive Grenzfälle-Analyse (Moduswechsel, kurze Zyklen).<br>
{{< /notice >}}

