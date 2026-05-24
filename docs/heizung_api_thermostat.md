## System- & Grundparameter

| Wert | Beschreibung |
|------|--------------|
| Letzter Fehler (lastcode) | Letzter Fehlercode inkl. Zeitraum |
| Datum/Zeit (datetime) | Aktuelle Systemzeit der Regelung |
| Korrektur interner Temperatur (intoffset) | Offset für internen Temperaturfühler |
| Estrichtrocknung (floordry) | Estrichtrocknungsprogramm aktiv/aus |
| Gedämpfte Außentemperatur (dampedoutdoortemp) | Gefilterte Außentemperatur |
| Estrichtrocknungstemperatur (floordrytemp) | Temperatur für Estrichtrocknung |
| Gebäudetyp (building) | Gebäudekategorie für Heizkurve |
| Min. Außentemperatur (minexttemp) | Untergrenze für Heizkurve |
| Dämpfung der Außentemperatur (damping) | Außentemperatur-Glättung aktiv |
| Solar (solar) | Solaranlage erkannt/aktiv |

## 🔥 Heizkreis 1 (HK1) – Raum & Betriebsparameter
| Wert | Beschreibung |
|------|--------------|
| HK1 gewählte Raumtemperatur (seltemp) | Aktuell eingestellte Raumtemperatur |
| HK1 Discovery aktuelle Raumtemperatur (haclimate) | Von Home Assistant erkannte Temperaturquelle |
| HK1 Betriebsart (mode) | Betriebsmodus (auto/manuell) |
| HK1 Modustyp (modetype) | Komfort/Eco/Manuell |
| HK1 eco Temperatur (ecotemp) | Eco-Temperatur |
| HK1 manuelle Temperatur (manualtemp) | Manuell eingestellte Temperatur |
| HK1 Komforttemperatur (comforttemp) | Komforttemperatur |
| HK1 Sommertemperatur (summertemp) | Außentemperaturgrenze Sommerbetrieb |
| HK1 Auslegungstemperatur (designtemp) | Max. Vorlauftemperatur bei tiefster Außentemperatur |
| HK1 Temperaturanhebung (offsettemp) | Offset für Heizkurve |
| HK1 min. Vorlauftemperatur (minflowtemp) | Mindest-Vorlauftemperatur |
| HK1 max. Vorlauftemperatur (maxflowtemp) | Maximal-Vorlauftemperatur |
| HK1 Raumeinfluss (roominfluence) | Raumeinfluss aktiv (0=aus) |
| HK1 Raumeinflussfaktor (roominflfactor) | Stärke des Raumeinflusses |
| HK1 aktueller Raumeinfluss (curroominfl) | Momentaner Einflusswert |
| HK1 Frostschutzmodus (nofrostmode) | Frostschutzart (Außen/Innen) |
| HK1 Frostschutztemperatur (nofrosttemp) | Frostschutztemperatur |
| HK1 berechnete Vorlauftemperatur (targetflowtemp) | Soll-Vorlauftemperatur laut Regelung |
| HK1 Heizungstyp (heatingtype) | Heizkörper/Fußbodenheizung |
| HK1 Einstellung Sommerbetrieb (summersetmode) | Einstellung Sommer/Winter |
| HK1 Sommerbetrieb (summermode) | Aktueller Sommer/Winterstatus |
| HK1 Urlaubsmodus (vacationmode) | Urlaubsmodus aktiv |
| HK1 Steuermodus (controlmode) | Regelungsart (z. B. witterungsgeführt) |
| HK1 Programm (program) | Zeitprogramm |
| HK1 temporäre Solltemperatur Automatikmodus (tempautotemp) | Temporäre Temperatur im Automatikmodus |
| HK1 Kühltemperatur (cooltemp) | Solltemperatur für Kühlbetrieb |
| HK1 schnelles Aufheizen (fastheatup) | Schnellaufheizfunktion |
| HK1 Einschaltoptimierung (switchonoptimization) | Optimiertes Einschalten |
| HK1 Absenkmodus (reducemode) | Reduzierter Modus |
| HK1 Durchheizen unter (noreducetemp) | Keine Absenkung unter dieser Temperatur |
| HK1 Absenkmodus unter (reducetemp) | Absenktemperatur |
| HK1 Kühlung an (coolingon) | Kühlfunktion aktiv |
| HK1 WP-Modus (hpmode) | Wärmepumpenmodus |
| HK1 Fernsteuerung (control) | Steuergerät (z. B. RC310) |
| HK1 Raumtemperatur Remote (remotetemp) | Remote-Raumtemperatur |
| HK1 Raumfeuchte Remote (remotehum) | Remote-Luftfeuchte |
| HK1 Schaltprogrammmodus (switchprogmode) | Level/Standard |
| HK1 Absenkschwelle (redthreshold) | Schwelle für Absenkbetrieb |
| HK1 Solareinfluß (solarinfl) | Solareinflussfaktor |
| HK1 akt. Solareinfluß (currsolarinfl) | Aktueller Solareinfluss |
| HK1 Heizungs-PID (heatingpid) | PID-Regelungsprofil |
| HK1 Pumpenoptimierung (pumpopt) | Pumpenoptimierung aktiv |
| HK1 Integralzeit (inttime) | PID-Integralzeit |

## 💧 Warmwasser (WWK)
| Wert | Beschreibung |
|------|--------------|
| WWK Betriebsart (mode) | Betriebsmodus (Eigenprogramm/Auto) |
| WWK Solltemperatur (settemp) | Zieltemperatur Warmwasser |
| WWK untere Solltemperatur (settemplow) | Untere Temperaturgrenze |
| WWK Zirkulationspumpenmodus (circmode) | Zirkulationsprogramm |
| WWK Ladedauer (chargeduration) | Dauer eines Ladevorgangs (Minuten) |
| WWK Laden (charge) | Warmwasserladung aktiv |
| WWK Extra (extra) | Extra-Ladung |
| WWK Desinfizieren (disinfecting) | Legionellenprogramm aktiv |
| WWK Desinfektionstag (disinfectday) | Wochentag für Desinfektion |
| WWK Desinfektionszeit (disinfecttime) | Dauer der Desinfektion (Minuten) |
| WWK täglich Heizen (dailyheating) | Tägliche Warmwasserladung |
| WWK tägliche Heizzeit (dailyheattime) | Dauer täglicher Warmwasserladung |
