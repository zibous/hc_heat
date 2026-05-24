# hc_haco2 – Heizungscontroller

IoT-Anwendung zur Erfassung, Berechnung und Visualisierung von Heizungsdaten
einer Buderus LOGAMAX PLUS GB172-14 Gasheizung.

## Hardware

- **Gastherme**: Buderus LOGAMAX PLUS GB172-14 (14 kW)
- **Warmwasserspeicher**: Geminox BS 150
- **Steuerung**: EMS-ESP32 (Firmware v3.8.1)
- **Gaszähler**: BK-G2,5 + IN-Z61 Sensor + ESPHome ESP32
- **Heizkörper**: 13 über 3 Geschosse

## App Flow

```
┌─────────────────────────────────────────────────────────┐
│                      app.py                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │ --once   │  │ --simulate   │  │ Produktivbetrieb  │ │
│  │ (einmal) │  │ (Testdaten)  │  │ (Hauptschleife)   │ │
│  └──────────┘  └──────────────┘  └─────────┬─────────┘ │
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
   │ Daten holen  │   │  Berechnen      │   │  Ausgeben     │
   └──────┬───────┘   └────────┬────────┘   └──────┬───────┘
          │                    │                    │
    ┌─────┴──────┐      ┌─────┴──────┐      ┌─────┴──────┐
    │ EMS-ESP32  │      │ Runtime    │      │ Dashboard  │
    │ /api/boiler│      │ Calc       │      │ :5028      │
    ├────────────┤      ├────────────┤      ├────────────┤
    │ EMS-ESP32  │      │ Consumption│      │ SQLite DB  │
    │ /api/therm.│      │ Calc       │      ├────────────┤
    ├────────────┤      ├────────────┤      │ MQTT       │
    │ ESPHome    │      │ Cost Calc  │      │ (optional) │
    │ Gasmeter   │      ├────────────┤      ├────────────┤
    └────────────┘      │ Error Log  │      │ Webhooks   │
                        └────────────┘      │ (optional) │
                                            ├────────────┤
                                            │ CSV Export │
                                            └────────────┘
```

## Hauptzyklus (alle 60s)

```
1. HTTP GET /api/boiler        → Boiler, System, HeatingCircuit, DHW
2. HTTP GET /api/thermostat    → Thermostat HC1, WWK
3. HTTP GET /text_sensor/gas   → Gaszähler (nur bei Brennerbetrieb + TTL)
4. Betriebsmodus bestimmen     → Standby / Heizung / Warmwasser / Desinfektion
5. In SQLite speichern         → data/heating.db
6. Verbrauch berechnen         → Periode, Heute, kumulativ
7. Kosten berechnen            → basierend auf costs.yaml Preisen
8. Fehler prüfen               → Kessel + Thermostat mit Klartext
9. Webhooks senden             → bei Änderungen an Home Assistant
10. MQTT publizieren           → optional, mit Auto-Reconnect
11. Dashboard aktualisieren    → Live-Daten Cache für Browser
```

## Projektstruktur

```
hc_heat2/
├── app.py                          # Entry-Point, CLI (--once), Signal-Handler
├── docker-compose.yml              # Docker Deployment
├── dockerfile                      # Container Image
├── Makefile                        # Build/Run/Test Befehle
├── requirements.txt                # Python Abhängigkeiten
├── .env                            # Konfiguration (nicht im Repo)
├── .env.example                    # Vorlage für .env
│
├── config/
│   ├── app_config.py               # Zentrale Konfiguration aus .env + YAML
│   ├── costs.yaml                  # Gas-/Energiepreise pro Periode
│   ├── field_mappings.yaml         # EMS-ESP API Keys → interne Feldnamen
│   └── lang/
│       └── errorcodes_de.yaml      # Buderus Fehlercodes (Deutsch)
│
├── lib/
│   ├── core/
│   │   ├── controller.py           # HeatingController (Hauptlogik)
│   │   ├── live_data_builder.py    # Dashboard-Dict Builder
│   │   ├── heating_system_manager.py # HTTP Datenabruf
│   │   ├── db_manager.py           # SQLite Zeitreihen-DB
│   │   ├── history_buffer.py       # DB → Dashboard Charts
│   │   ├── history_manager.py      # JSON Snapshot Export
│   │   ├── history_writer.py       # CSV History Writer (wöchentlich)
│   │   └── errorcodes.py           # Fehlercode-Übersetzung
│   │
│   ├── models/                     # Datenklassen (Dataclasses)
│   │   ├── boiler.py               # Kessel (28 Felder)
│   │   ├── dhw.py                  # Warmwasser
│   │   ├── disinfection.py         # Desinfektion
│   │   ├── gas_meter.py            # Gaszähler
│   │   ├── heating_circuit.py      # Heizkreis
│   │   ├── heating_snapshot.py     # Komplett-Snapshot
│   │   ├── heating_system.py       # System-Container
│   │   ├── operation_state.py      # Betriebszustand
│   │   ├── system_data.py          # Systemparameter
│   │   └── thermostat.py           # Thermostat RC310
│   │
│   ├── calc/                       # Berechnungsmodule
│   │   ├── consumption_calc.py     # Verbrauch nach Betriebsart
│   │   ├── cost_calc.py            # Kosten pro Periode
│   │   ├── runtime_calc.py         # Laufzeiten + Betriebsmodus
│   │   └── error_log.py            # Fehler-Tracking mit Klartext
│   │
│   ├── utils/
│   │   ├── helpers.py              # Typkonvertierung, Timestamp-Parser
│   │   ├── field_mapper.py         # YAML-basiertes Feld-Mapping
│   │   ├── env_loader.py           # .env Loader (ohne Abhängigkeit)
│   │   ├── logging_setup.py        # Logging-Konfiguration
│   │   └── flow_tracer.py          # Debug Flow-Trace
│   │
│   ├── dashboard_server.py         # HTTP Server für Dashboard + API
│   ├── mqttclient.py               # MQTT mit Auto-Reconnect
│   └── webhooks.py                 # Home Assistant Webhook Events
│
├── dashboard/static/
│   └── index.html                  # Dashboard (Single-Page, Chart.js)
│
├── data/
│   ├── heating.db                  # Produktiv-Datenbank (SQLite)
│   ├── heating_sim.db              # Simulate-Datenbank
│   ├── meter_readings.yaml         # Zählerstände Periodenbeginn
│   └── raw/                        # EMS-ESP Rohdaten (Referenz)
│
├── scripts/
│   ├── simulate.py                 # 14 Tage Testdaten generieren
│   └── export_history.py           # History-CSV aus DB exportieren
│
└── testcases/
    └── test_offline.py             # Offline-Tests (97 Checks)
```

## Befehle

| Befehl | Aktion |
|---|---|
| `make run` | Produktivbetrieb starten |
| `make once` | Einmaliger Datenabruf (Terminal-Ausgabe) |
| `make simulate` | 14 Tage Testdaten + Dashboard |
| `make test` | Offline-Tests (Models, Helpers, Config) |
| `make build` | Docker Image bauen |
| `make up` | Docker Container starten |
| `make down` | Docker Container stoppen |
| `make resetdb` | Produktiv-DB löschen |
| `python3 scripts/export_history.py` | History-CSV aus DB exportieren |
| `make clean` | Cache/Temp löschen |
| `make help` | Alle Befehle anzeigen |

## Konfiguration

### .env (Hauptkonfiguration)

Alle Einstellungen über Umgebungsvariablen. Siehe `.env.example`.

### config/costs.yaml (Preise)

Gaspreise pro Abrechnungszeitraum (01.09.–31.08.), Energiepreise pro Kalenderjahr.
Die App wählt automatisch den passenden Preis für das aktuelle Datum.

### config/field_mappings.yaml (API-Keys)

Mapping zwischen EMS-ESP JSON-Keys und internen Feldnamen.
Bei Firmware-Update nur die YAML anpassen, kein Python-Code nötig.

### config/lang/errorcodes_de.yaml (Fehlercodes)

Buderus Fehlercodes mit deutschen Klartext-Beschreibungen.

### data/meter_readings.yaml (Zählerstände)

Zählerstände zu Beginn der Abrechnungsperioden für Verbrauchs-/Kostenberechnung.

## Datenfluss

```
EMS-ESP32                    ESPHome ESP32
(Heizung)                    (Gaszähler)
    │                             │
    │ HTTP /api/boiler            │ HTTP /text_sensor/gasmeterdata
    │ HTTP /api/thermostat        │ (nur bei Brennerbetrieb + 30s TTL)
    │                             │
    └──────────┬──────────────────┘
               │
    ┌──────────▼──────────┐
    │ HeatingSystemManager │  ← 1x Boiler-Request für System+Boiler+HC
    │ (1 Zyklus = 2-3 HTTP)│  ← 1x Thermostat-Request
    └──────────┬──────────┘  ← 0-1x Gasmeter (bedingt)
               │
    ┌──────────▼──────────┐
    │ Field Mapper         │  ← field_mappings.yaml
    │ (YAML → Dataclass)   │  ← Thermostat: Langname-Keys normalisiert
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Models (Dataclasses) │
    │ Boiler, DHW, System, │
    │ HeatingCircuit, Gas,  │
    │ Thermostat            │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Calculators          │
    │ Runtime → Modus      │  Standby/Heizung/WW/Desinfektion
    │ Consumption → kWh    │  Gesamt, Heizung, WW, Desinfektion
    │ Cost → EUR           │  basierend auf costs.yaml
    │ ErrorLog → Klartext  │  basierend auf errorcodes_de.yaml
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │ Ausgabe              │
    │ ├─ SQLite DB         │  data/heating.db (Zeitreihe)
    │ ├─ Dashboard         │  :5028/dashboardhaco (Live + Charts)
    │ ├─ MQTT              │  optional, Auto-Reconnect
    │ └─ Webhooks          │  optional, bei Änderungen → HA
    └─────────────────────┘
```

## Dashboard

Erreichbar unter `http://<server>:5028/dashboardhaco`

### Bereiche

1. **Status-Leiste**: Modus, Brenner, Pumpe, Heute Energie/Gas/Kosten
2. **Heizungsanlage**: Flowchart Gas → Therme → Heizkörper/WW/Desinfektion
3. **Temperaturen**: Vorlauf, WW, Außen mit Trend (▲▼●)
4. **Temperaturverlauf**: 14-Tage Linien-Chart
5. **Heizkurve**: Scatter Außentemp → Vorlauf (nur Heizbetrieb)
6. **Energie/Kosten**: Perioden-Tabs (Heute/7T/Monat/Jahr/Zeitraum), Balken-Chart + CSV-Export
7. **Erweiterte Werte**: Fehler, Kessel, WW, Gaszähler, Thermostat

### Features

- Dark/Light Theme (gespeichert in localStorage)
- Perioden-Auswahl gespeichert in localStorage
- Auto-Refresh (konfigurierbar über INTERVALL)
- Cache-Busting (Timestamp an API-Aufrufe)
- Responsive (Desktop + Mobile)
- CSV-Export (Semikolon, deutsches Dezimalkomma, UTF-8 BOM)

## MQTT (optional)

Verbindet sich zu einem bestehenden Broker wenn `MQTT_HOST` in `.env` gesetzt ist.

- Auto-Reconnect mit paho.mqtt (5s–120s Backoff)
- Periodischer Reconnect-Versuch alle 5 Minuten
- Nach 30 Minuten ohne Verbindung: MQTT deaktiviert + Webhook an HA
- Duplikat-Check (gleiche Payload wird nicht erneut gesendet)

## Home Assistant Webhooks (optional)

Sendet Events bei Änderungen wenn `HA_WEBHOOK_URL` und `HA_WEBHOOK_ID` gesetzt:

| Event | Trigger |
|---|---|
| `mode_changed` | Betriebsmodus geändert |
| `error_boiler` | Neuer Kessel-Fehlercode |
| `error_thermostat` | Neuer Thermostat-Fehlercode |
| `temp_warning` | WW-Temp < (Offset - 5°C) |
| `system_ok` | Temperatur wieder normal |
| `mqtt_unavailable` | MQTT nach 30 min aufgegeben |

## Gaszähler-Steuerung

Der ESPHome Gaszähler wird nur abgefragt wenn:
- Brenner aktiv ist, ODER
- Brenner vor weniger als `GAS_TTL` Sekunden (default 30s) aktiv war

Das schont den ESP32 und verhindert Instabilität bei zu vielen Anfragen.

## History CSV

Wöchentliche CSV-Dateien in `data/history/` für Replay und Analyse.

### Konfiguration (.env)

```env
SAVE_HISTORY=true              # History aktivieren (default: true)
HISTORY_DIR=./data/history     # Verzeichnis
HISTORY_KEEP_WEEKS=8           # Alte Dateien nach N Wochen löschen
```

### Format

Semikolon-getrennt, 16 Spalten pro Zeile:

```
ts;mode;outdoor_temp;flow_temp;flow_set_temp;target_flow_temp;dhw_temp;dhw_set_temp;burner_active;burner_power;pump_active;pump_modulation;energy_total_kwh;energy_heat_kwh;energy_dhw_kwh;gas_display_m3
2026-05-04T10:15:58;standby;17.2;32.5;28.0;;59.7;57.0;0;0;1;41;15916.28;11169.01;4747.4;32385.1
```

Dateinamen: `YYYY-WNN.csv` (z.B. `2026-W18.csv`)

### API-Endpunkte

| Endpunkt | Beschreibung |
|---|---|
| `GET /api/history-files` | Liste der verfügbaren CSV-Dateien |
| `GET /api/history-file?name=2026-W18.csv` | CSV-Datei herunterladen |

### Export aus DB

Bestehende DB-Daten als History-CSV exportieren:

```bash
# Alle Daten
python3 scripts/export_history.py

# Letzte 7 Tage
python3 scripts/export_history.py --days 7

# Bestimmter Zeitraum
python3 scripts/export_history.py --from 2026-05-01 --to 2026-05-04

# In anderen Ordner (zum Vergleich mit Live-Daten)
python3 scripts/export_history.py --out ./data/history_db
```

Das Script zeigt zusätzlich eine Grenzfälle-Analyse:
- Moduswechsel-Häufigkeit (z.B. `standby → heating: 45x`)
- Kürzester/längster/durchschnittlicher Zyklus pro Modus
- Kurze Zyklen (<2 min) die auf Polling-Probleme hindeuten
- Temperatur-Extremwerte und Gesamtverbrauch

## Datenbank

SQLite in `data/heating.db`. Eine Zeile pro Zyklus (alle 60s).

- ~525.000 Zeilen/Jahr (~50 MB)
- Automatisches Backup beim Start (`heating.db.bak`)
- Automatischer Cleanup: Daten älter als 2 Jahre werden gelöscht
- Separate DB für Simulate: `heating_sim.db`
