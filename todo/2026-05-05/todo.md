# Dashboard hc_heat2

## Heizungsanlage

   - Darstellung geht nicht auf den Handy Xiaomi Redmi Note 13 Pro.
    - Wenn quer ansicht (Handy gedreht) ist die Ansicht Heizungsanlage sichtbar.
    - Beim refresh nicht mehr
    - Hochkant nicht sichtbar
    - Farbwechsel Hintergrundfarbe Betriebsanzeige geht nicht, es werdn nur
      die Rahmenfarben geändert.
      
   - Erweiterungen
     - WARNUNG: Anzeige Fehlercodes + Text wenn neu ganz unten nach Schema Heizungsanlage
       INFO:    wenn keiner "Heizungsanlage läuft und arbeitet einwandfrei" (aus lang.de)
     - Progressbar Timeline die Verarbeiung der Datenbeschaffung vür 24h
       Soll zeigen wie die Anfragen seit 0:00 des laufenden Tages geht.
       Min: 0, Max: 24h * Intervalle, Wert: Anzahl der Abfrage Intervalle

       Beispiel  Start | ---------                            | Ende


 ## Kacheln oben erweitern alle im Aussehen wie die bereits vorhandenen.
    - Anzahl Fehler (Anzahl und letzer am)
    - Heizbetrieb (Sommer / Winter)
    - Informationen Betriebszeiten
      - Installiert seit Tage, Stunden
      - Anteil Heizung gesamt,  Betriebsmode
    - Status Heizsystem EMS ESP32 (HEATING_INFO)
    - Status Boiler (HEATING_SENSOR)
    - Status Thermostat (HEATING_THERMOSTAT)
    - Status GAS Zähler

