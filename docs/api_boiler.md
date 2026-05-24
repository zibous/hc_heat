# Heizungsanlage

## Ermittlung Betriebszustand

| Priorität | Modus | Logik / Bedingung | Erklärung |
|-----------|--------|--------------------|-----------|
| 1 | **Desinfektion** | dhw.disinfecting == true | Legionellenprogramm aktiv. Warmwasser wird auf 60–70°C erhitzt. Höchste Priorität. |
| 2 | **Warmwasserbereitung** | dhw.disinfecting == false AND tapwateractive == "an" | Speicherladung aktiv. 3‑Wege‑Ventil steht auf Warmwasser. Brenner läuft meist hoch. |
| 3 | **Heizkörperbetrieb** | heatingactive == "an" AND dhw.disinfecting == false AND tapwateractive == "aus" | Heizbetrieb aktiv. Vorlauftemperatur wird nach Heizkurve erzeugt. |
| 4 | **Standby / Bereitschaft** | dhw.disinfecting == false AND tapwateractive == "aus" AND heatingactive == "aus" | Keine Anforderung. Nur Pumpennachlauf oder Bereitschaft. |

### Logik

1. Desinfektion ist immer eindeutig
2. Warmwasser hat immer Vorrang vor Heizen
3. Heizbetrieb ist eindeutig
4. Standby ist der Restzustand (keine Desinfektion, kein Warmwasser, kein Heizbetrieb)


## 🔥 1. Boiler / Kessel
| Wert | Technische Erklärung |
|------|----------------------|
| reset | Interner Resetstatus der UBA/BCU. Leer = kein Reset. Wird bei Fehlern oder Firmwareupdates gesetzt. |
| heatingoff | Signalisiert, dass der Heizbetrieb softwareseitig deaktiviert ist. Hat Vorrang vor Heizanforderungen. |
| heatingactive | Zeigt, ob der Kessel aktuell Wärme für den Heizkreis erzeugt. Wird durch Heizkurve + Raumregelung bestimmt. |
| tapwateractive | Warmwasseranforderung aktiv. Priorisiert gegenüber Heizung (Warmwasser hat Vorrang). |
| selflowtemp | Soll-Vorlauftemperatur, die die Regelung berechnet (Heizkurve + Außentemperatur + Raumeinfluss). |
| heatingpumpmod | Modulation der Heizkreispumpe in %. Moderne Pumpen arbeiten drehzahlgeregelt (PWM/0–10V). |
| outdoortemp | Außentemperatur vom Außensensor. Grundlage für witterungsgeführte Regelung. |
| curflowtemp | Tatsächliche Vorlauftemperatur. Wird vom Kesseltemperatursensor gemessen. |
| burngas | Gasventil geöffnet, Brenner aktiv. |
| burngas2 | Zweiter Brennerstufe aktiv (bei 2-stufigen Geräten). |
| flamecurr | Flammenstrom in µA. Wichtiger Parameter für Verbrennungsqualität und Ionisation. |
| fanwork | Gebläse läuft. Notwendig für Verbrennungsluft und Abgastransport. |
| ignwork | Zündtrafo aktiv. Nur beim Start. |
| oilpreheat | Vorwärmung für Ölbrenner (bei Gasgeräten immer „aus“). |
| burnminpower | Untere Modulationsgrenze des Brenners. Zu niedrig → Takten. |
| burnmaxpower | Maximale Brennerleistung. Wird bei Warmwasser oft voll genutzt. |
| burnminperiod | Mindestlaufzeit, um Takten zu reduzieren. |
| boilhyston | Temperaturdifferenz, bei der der Brenner wieder einschaltet. |
| boilhystoff | Temperaturdifferenz, bei der der Brenner abschaltet. |
| curveon | Heizkurve aktiv. Ohne Heizkurve → reine Raumregelung. |
| curvebase | Vorlauftemperatur bei hoher Außentemperatur (z. B. +20°C). |
| curveend | Vorlauftemperatur bei tiefster Außentemperatur (z. B. –10°C). |
| summertemp | Außentemperatur, ab der Heizung komplett deaktiviert wird. |
| nofrostmode | Frostschutz aktiv (Außen/Innen). |
| nofrosttemp | Temperatur, bei der Frostschutz anspringt. |
| heatingactivated | Heizbetrieb grundsätzlich aktiviert (Master-Schalter). |
| heatingtemp | Zieltemperatur des Kessels für Heizbetrieb. |
| heatingpump | Heizkreispumpe läuft. |
| pumpmodmax | Maximal erlaubte Pumpenmodulation. |
| pumpmodmin | Minimal erlaubte Pumpenmodulation. |
| pumpmode | Pumpenregelung: deltaP = Differenzdruckregelung. |
| pumpdelay | Nachlaufzeit der Pumpe nach Brennerstop. Verhindert Überhitzung. |
| pumpontemp | Temperatur, ab der die Pumpe startet. |
| selburnpow | Vom Regler gewählte Brennerleistung. |
| curburnpow | Tatsächlich gefahrene Brennerleistung. |
| burnstarts | Anzahl Brennerstarts. Hohe Zahl = Takten = ineffizient. |
| burnworkmin | Gesamtlaufzeit des Brenners. |
| heatworkmin | Laufzeit im Heizbetrieb. |
| ubauptime | Betriebszeit der Steuerung (UBA). |
| lastcode | Letzter Fehler inkl. Zeit. Wichtig für Diagnose. |
| servicecode | Interner Servicestatus. |
| maintenancemessage | Wartungsmeldung (z. B. H00 = keine Wartung nötig). |
| maintenancedate | Nächstes Wartungsdatum. |
| nompower | Nennleistung des Kessels in kW. |
| nrgtotal | Gesamtenergieverbrauch (Heizung + Warmwasser). |
| nrgheat | Energieverbrauch nur Heizung. |


### GB172‑14 spezifisch

| Wert | Technische Erklärung (GB172‑14 spezifisch) |
|------|--------------------------------------------|
| reset | Interner Resetstatus der UBA3. Wird bei Fehlern oder Firmwareupdates gesetzt. |
| heatingoff | Heizbetrieb softwareseitig deaktiviert. Hat Vorrang vor Heizanforderungen. |
| heatingactive | Kessel erzeugt aktiv Heizwärme. Wird durch Heizkurve + Raumregelung bestimmt. |
| tapwateractive | Warmwasserbereitung aktiv. Beim GB172 hat Warmwasser immer Priorität. |
| selflowtemp | Soll-Vorlauftemperatur laut Heizkurve + Gebäudetyp + Raumeinfluss. |
| heatingpumpmod | Modulation der internen PWM-Pumpe. GB172 nutzt deltaP-Regelung. |
| outdoortemp | Außentemperatur vom Sensor. Basis für witterungsgeführte Regelung. |
| curflowtemp | Tatsächliche Vorlauftemperatur. Wird vom Kesseltemperatursensor gemessen. |
| burngas | Gasventil geöffnet, Brenner aktiv. |
| burngas2 | Zweite Brennerstufe (GB172 hat nur 1-stufig modulierend → meist „aus“). |
| flamecurr | Ionisationsstrom. Beim GB172 ungewöhnlich hoch (20–35 µA normal). |
| fanwork | Gebläse läuft. Notwendig für Verbrennungsluft und Abgastransport. |
| ignwork | Zündtrafo aktiv. Nur beim Start. |
| oilpreheat | Nur bei Ölkesseln relevant → beim GB172 immer „aus“. |
| burnminpower | Untere Modulationsgrenze (~20–25 % real). |
| burnmaxpower | Maximale Brennerleistung (100 % = 14 kW). |
| burnminperiod | Mindestlaufzeit, um Takten zu reduzieren. GB172 hat kurze Mindestlaufzeit. |
| boilhyston | Einschalt-Hysterese (typisch 6 K). |
| boilhystoff | Ausschalt-Hysterese. GB172 arbeitet mit enger Hysterese → häufige Starts. |
| curveon | Heizkurve aktiv. Ohne Heizkurve → reine Raumregelung. |
| curvebase | Vorlauftemperatur bei hoher Außentemperatur. |
| curveend | Vorlauftemperatur bei tiefster Außentemperatur. |
| summertemp | Außentemperaturgrenze für Sommerabschaltung. |
| nofrostmode | Frostschutz aktiv (Außen/Innen). |
| nofrosttemp | Temperatur, bei der Frostschutz anspringt. |
| heatingactivated | Heizbetrieb grundsätzlich aktiviert (Master-Schalter). |
| heatingtemp | Zieltemperatur des Kessels für Heizbetrieb. |
| heatingpump | Heizkreispumpe läuft. |
| pumpmodmax | Maximal erlaubte Pumpenmodulation. |
| pumpmodmin | Minimal erlaubte Pumpenmodulation. |
| pumpmode | Pumpenregelung: deltaP-2 = Differenzdruckregelung mit Heizkurvenanpassung. |
| pumpdelay | Pumpennachlaufzeit. GB172 nutzt langen Nachlauf für Brennwertnutzung. |
| pumpontemp | Temperatur, ab der die Pumpe startet. |
| selburnpow | Vom Regler gewählte Brennerleistung. |
| curburnpow | Tatsächlich gefahrene Brennerleistung. |
| burnstarts | Anzahl Brennerstarts. GB172 neigt zum Takten → hoher Wert typisch. |
| burnworkmin | Gesamtlaufzeit des Brenners. |
| heatworkmin | Laufzeit im Heizbetrieb. |
| ubauptime | Betriebszeit der UBA-Steuerung. |
| lastcode | Letzter Fehler inkl. Zeit. Wichtig für Diagnose. |
| servicecode | Interner Servicestatus. |
| maintenancemessage | Wartungsmeldung (z. B. H00 = keine Wartung nötig). |
| maintenancedate | Nächstes Wartungsdatum. |
| nompower | Nennleistung des Kessels (14 kW). |
| nrgtotal | Gesamtenergieverbrauch (Heizung + Warmwasser). |
| nrgheat | Energieverbrauch nur Heizung. |


## 🌡️ 2. Thermostat / Heizkreis 1 (HK1)
| Wert | Technische Erklärung |
|------|----------------------|
| seltemp | Zieltemperatur, die der Nutzer eingestellt hat. |
| haclimate | Von Home Assistant erkannte Temperaturquelle (z. B. Solltemperatur). |
| mode | Automatik/Manuell. Automatik nutzt Zeitprogramme. |
| modetype | Komfort/Eco/Manuell – beeinflusst Heizkurve. |
| ecotemp | Temperatur im Eco-Modus (Absenkbetrieb). |
| manualtemp | Temperatur im manuellen Modus. |
| comforttemp | Komforttemperatur (höchste Stufe). |
| summertemp | Außentemperaturgrenze für Sommerabschaltung. |
| designtemp | Vorlauftemperatur bei tiefster Außentemperatur. |
| offsettemp | Offset zur Heizkurve (Feinjustierung). |
| minflowtemp | Mindest-Vorlauftemperatur für HK1. |
| maxflowtemp | Maximal-Vorlauftemperatur für HK1. |
| roominfluence | Raumeinfluss aktiv (0 = aus). |
| roominflfactor | Stärke des Raumeinflusses (1–10). |
| curroominfl | Momentaner Einflusswert. |
| nofrostmode | Frostschutzart (Außen/Innen). |
| nofrosttemp | Temperatur für Frostschutz. |
| targetflowtemp | Berechnete Vorlauftemperatur (Heizkurve + Raum). |
| heatingtype | Heizkörper/Fußbodenheizung. |
| summersetmode | Einstellung Sommer/Winter. |
| summermode | Aktueller Sommer/Winterstatus. |
| vacationmode | Urlaubsmodus aktiv. |
| controlmode | Regelungsart: witterungsgeführt, raumgeführt, kombiniert. |
| program | Zeitprogramm (z. B. prog 1). |
| tempautotemp | Temporäre Temperatur im Automatikmodus. |
| cooltemp | Zieltemperatur für Kühlbetrieb (falls WP). |
| fastheatup | Schnellaufheizfunktion (Boost). |
| switchonoptimization | Optimiertes Einschalten (lernt Heizverhalten). |
| reducemode | Reduzierter Betrieb (Eco). |
| noreducetemp | Keine Absenkung unter dieser Temperatur. |
| reducetemp | Absenktemperatur. |
| coolingon | Kühlfunktion aktiv. |
| hpmode | Wärmepumpenmodus (Heizen/Kühlen). |
| control | Fernsteuergerät (z. B. RC310). |
| remotetemp | Remote-Raumtemperatur (falls vorhanden). |
| remotehum | Remote-Luftfeuchte. |
| switchprogmode | Level/Standard – beeinflusst Zeitprogrammstruktur. |
| redthreshold | Schwelle für Absenkbetrieb. |
| solarinfl | Solareinflussfaktor (z. B. Sonneneinstrahlung). |
| currsolarinfl | Aktueller Solareinfluss. |
| heatingpid | PID-Regelprofil (z. B. Mittel). |
| pumpopt | Optimierung der Pumpenlaufzeit. |
| inttime | Integralzeit des PID-Reglers. |


### GB172‑14 spezifisch

| Wert | Technische Erklärung |
|------|----------------------|
| seltemp | Zieltemperatur, die der Nutzer eingestellt hat. |
| haclimate | Von Home Assistant erkannte Temperaturquelle. |
| mode | Automatik/Manuell. Automatik nutzt Zeitprogramme. |
| modetype | Komfort/Eco/Manuell – beeinflusst Heizkurve. |
| ecotemp | Temperatur im Eco-Modus (Absenkbetrieb). |
| manualtemp | Temperatur im manuellen Modus. |
| comforttemp | Komforttemperatur (höchste Stufe). |
| summertemp | Außentemperaturgrenze Sommerabschaltung. |
| designtemp | Vorlauftemperatur bei tiefster Außentemperatur. |
| offsettemp | Offset zur Heizkurve (Feinjustierung). |
| minflowtemp | Mindest-Vorlauftemperatur für HK1. |
| maxflowtemp | Maximal-Vorlauftemperatur für HK1. |
| roominfluence | Raumeinfluss aktiv (0 = aus). |
| roominflfactor | Stärke des Raumeinflusses (1–10). |
| curroominfl | Momentaner Einflusswert. |
| nofrostmode | Frostschutzart (Außen/Innen). |
| nofrosttemp | Temperatur für Frostschutz. |
| targetflowtemp | Berechnete Vorlauftemperatur (Heizkurve + Raum). |
| heatingtype | Heizkörper/Fußbodenheizung. |
| summersetmode | Einstellung Sommer/Winter. |
| summermode | Aktueller Sommer/Winterstatus. |
| vacationmode | Urlaubsmodus aktiv. |
| controlmode | Regelungsart: witterungsgeführt, raumgeführt, kombiniert. |
| program | Zeitprogramm (z. B. prog 1). |
| tempautotemp | Temporäre Temperatur im Automatikmodus. |
| cooltemp | Zieltemperatur für Kühlbetrieb (falls WP). |
| fastheatup | Schnellaufheizfunktion (Boost). |
| switchonoptimization | Optimiertes Einschalten (lernt Heizverhalten). |
| reducemode | Reduzierter Betrieb (Eco). |
| noreducetemp | Keine Absenkung unter dieser Temperatur. |
| reducetemp | Absenktemperatur. |
| coolingon | Kühlfunktion aktiv. |
| hpmode | Wärmepumpenmodus (Heizen/Kühlen). |
| control | Fernsteuergerät (z. B. RC310). |
| remotetemp | Remote-Raumtemperatur (falls vorhanden). |
| remotehum | Remote-Luftfeuchte. |
| switchprogmode | Level/Standard – beeinflusst Zeitprogrammstruktur. |
| redthreshold | Schwelle für Absenkbetrieb. |
| solarinfl | Solareinflussfaktor (z. B. Sonneneinstrahlung). |
| currsolarinfl | Aktueller Solareinfluss. |
| heatingpid | PID-Regelprofil (z. B. Mittel). |
| pumpopt | Optimierung der Pumpenlaufzeit. |
| inttime | Integralzeit des PID-Reglers. |


## 💧 3. Warmwasser (WWK) 
| Wert | Technische Erklärung |
|------|----------------------|
| mode | Betriebsart (Eigenprogramm/Auto). |
| settemp | Zieltemperatur Warmwasser. |
| settemplow | Untere Temperaturgrenze (Hysterese). |
| circmode | Zirkulationspumpenprogramm. |
| chargeduration | Dauer eines Warmwasser-Ladevorgangs. |
| charge | Warmwasserladung aktiv. |
| extra | Extra-Ladung (Boost). |
| disinfecting | Legionellenprogramm aktiv. |
| disinfectday | Wochentag für Legionellenschutz. |
| disinfecttime | Dauer der Desinfektion. |
| dailyheating | Tägliche Warmwasserladung aktiv. |
| dailyheattime | Dauer der täglichen Warmwasserladung. |


### GB172‑14 spezifisch

| Wert | Technische Erklärung |
|------|----------------------|
| mode | Betriebsart (Eigenprogramm/Auto). |
| settemp | Zieltemperatur Warmwasser. |
| settemplow | Untere Temperaturgrenze (Hysterese). |
| circmode | Zirkulationspumpenprogramm. |
| chargeduration | Dauer eines Warmwasser-Ladevorgangs. |
| charge | Warmwasserladung aktiv. |
| extra | Extra-Ladung (Boost). |
| disinfecting | Legionellenprogramm aktiv. |
| disinfectday | Wochentag für Legionellenschutz. |
| disinfecttime | Dauer der Desinfektion. |
| dailyheating | Tägliche Warmwasserladung aktiv. |
| dailyheattime | Dauer der täglichen Warmwasserladung. |
