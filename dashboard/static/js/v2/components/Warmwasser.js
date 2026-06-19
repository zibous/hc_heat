// components/Warmwasser.js
export class Warmwasser {
    render() {
        return `
            <g id="comp-ww">
                <!-- Warmwasserspeicher BS 150 -->
                <rect id="box-speicher" x="80" y="220" width="180" height="105" class="bx" />
                <text x="170" y="242" text-anchor="middle" class="sv">BS 150</text>
                <circle id="dot-ww" cx="248" cy="232" r="4" fill="#64748b"/>

                <!-- Dynamische Speicher-Zeile mit integriertem Vektor-Tropfen -->
                <g id="speicher-werte-group">
                    <g id="speicher-icon-container" transform="translate(100, 247)">
                        <path d="M12 22a7 7 0 0 0 7-7c0-4.3-7-13-7-13S5 10.7 5 15a7 7 0 0 0 7 7z" fill="currentColor" stroke="none"/>
                    </g>
                    <text id="speicher-werte" x="122" y="259" class="st">--°C · Soll --°C</text>
                </g>

                <text id="speicher-status" x="170" y="276" text-anchor="middle" class="su">Bereit</text>
                <rect x="95" y="285" width="150" height="4" rx="2" class="bg-bar" />
                <rect id="bar-speicher" x="95" y="285" width="150" height="4" rx="2" class="p-blue" />

                <!-- Rohrleitung & Pfeil -->
                <line id="rohr-ww-speisung" x1="260" y1="270" x2="470" y2="270" class="pipe" />
                <polygon id="pfeil-ww" points="465,265 475,270 465,275" class="bg-bar" />

                <!-- Verbrauchsanzeige Warmwasser -->
                <rect id="box-ww" x="480" y="245" width="250" height="150" class="bx" />

                <!-- Modernes Dusch-Icon -->
                <g class="icon-svg" transform="translate(500, 256)">
                    <path d="M4 4h16v2H4z" fill="currentColor"/>
                    <path d="M12 6v6M8 14v4M12 14v4M16 14v4M6 14v2M18 14v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </g>
                <text x="530" y="271" class="sv">Warmwasser</text>

                <text id="ww-werte" x="605" y="288" text-anchor="middle" class="su">--°C</text>
                <rect x="510" y="297" width="190" height="4" rx="2" class="bg-bar" />
                <rect id="bar-ww" x="510" y="297" width="0" height="4" rx="2" class="p-blue" />
                <text id="ww-zeit" x="605" y="317" text-anchor="middle" class="sl">Letzter: --:-- · --m</text>
                <text id="ww-verbrauch" x="605" y="333" text-anchor="middle" class="sl">--,-- kWh · --,--- m³</text>

                <!-- Kaltwasseranschluss -->
                <line x1="170" y1="325" x2="170" y2="400" class="pipe" style="stroke:#06b6d4" />
                <text x="185" y="390" class="sl" style="fill:#06b6d4">Kaltwasser</text>
            </g>
        `;
    }

    /**
     * Aktualisiert die Warmwasser-Anzeigen im SVG basierend auf der data.json
     * @param {boolean} aktiv - Fallback-Vorgabe der Steuerungskomponente
     * @param {Object} data - Das rohe Server-JSON Objekt
     * @param {SVGElement} svg - Die Referenz auf das übergeordnete SVG-Element
     */
    set(aktiv, data = {}, svg) {
        if (!svg) return;

        const boxSpeicher = svg.querySelector('#box-speicher');
        const boxWw = svg.querySelector('#box-ww');
        const speicherWerte = svg.querySelector('#speicher-werte');
        const speicherStatus = svg.querySelector('#speicher-status');
        const speicherIcon = svg.querySelector('#speicher-icon-container');
        const wwWerte = svg.querySelector('#ww-werte');
        const wwZeit = svg.querySelector('#ww-zeit');
        const wwVerbrauch = svg.querySelector('#ww-verbrauch');
        const rohrWw = svg.querySelector('#rohr-ww-speisung');
        const pfeilWw = svg.querySelector('#pfeil-ww');
        const wwBalken = svg.querySelector('#bar-ww');
        const comp = svg.querySelector('#comp-ww');

        // Hilfsfunktion zur Formatierung nach deutscher Ländernorm (Komma statt Punkt)
        const formatNum = (val, dec = 1) => val !== undefined && val !== null ? val.toFixed(dec).replace('.', ',') : '--';

        // 1. Datenpfade aus der echten JSON-Struktur extrahieren
        const dhw = data.dhw || {};
        const today = data.today || {};
        const lastCycle = data.last_cycles?.dhw || {};

        // Warmwasserbereitung läuft wenn der Server "charging" meldet, das "aktiv" Flag gesetzt ist ODER Modus "dhw" ist
        const istWwAktiv = dhw.charging || aktiv || data.mode === 'dhw';

        // 2. Speicher-Inhalte (BS 150) einpflegen
        if (speicherWerte) {
            speicherWerte.textContent = `${formatNum(dhw.curtemp)}°C · Soll ${formatNum(dhw.settemp, 0)}°C`;
        }
        if (speicherStatus) {
            speicherStatus.textContent = istWwAktiv ? 'Lädt...' : 'Bereit';
        }

        // 3. Verbrauchsanzeige Warmwasser (Kachel rechts) einpflegen
        if (wwWerte) {
            wwWerte.textContent = `${formatNum(dhw.curtemp)}°C`;
        }

        // Letzten Zyklus parsen und lesbare Uhrzeit (HH:MM) extrahieren
        if (wwZeit) {
            let zeitString = '--:--';
            if (lastCycle.start) {
                const dateObj = new Date(lastCycle.start);
                if (!isNaN(dateObj.getTime())) {
                    zeitString = `${dateObj.getHours().toString().padStart(2, '0')}:${dateObj.getMinutes().toString().padStart(2, '0')}`;
                }
            }
            const dauerMin = lastCycle.duration_min ? Math.round(lastCycle.duration_min) : '--';
            wwZeit.textContent = `Letzter: ${zeitString} · ${dauerMin}m`;
        }

        // Verbrauchswerte für den heutigen Tag ausgeben
        if (wwVerbrauch) {
            wwVerbrauch.textContent = `${formatNum(today.dhw_kwh, 2)} kWh · ${formatNum(today.gas_m3, 3)} m³`;
        }

        // 4. Fortschrittsbalken und Breitenattribute manipulieren
        if (wwBalken) {
            wwBalken.setAttribute('width', istWwAktiv ? '190' : '0');
        }

        // 5. Dynamische Zentrierung des Speichertropfens basierend auf der Textlänge
        if (speicherWerte && speicherIcon) {
            const textLaenge = speicherWerte.textContent.length;
            const startX = 170 - (textLaenge * 3.3);
            speicherIcon.setAttribute('transform', `translate(${startX - 15}, 248) scale(0.7)`);
            speicherWerte.setAttribute('x', startX.toString());
        }

        // 6. Visuelle Statusklassen und Theme-Farbvariablen toggeln
        if (boxSpeicher) boxSpeicher.classList.toggle('active-ww', istWwAktiv);
        if (boxWw) boxWw.classList.toggle('active-ww', istWwAktiv);

        if (speicherWerte) {
            speicherWerte.style.fill = istWwAktiv ? 'var(--accent, #3b82f6)' : '';
        }

        if (comp) {
            comp.style.color = istWwAktiv ? 'var(--accent, #3b82f6)' : 'var(--text, #e2e8f0)';
        }

        // Status-Punkt
        const dot = svg.querySelector('#dot-ww');
        if (dot) dot.setAttribute('fill', istWwAktiv ? '#10b981' : '#64748b');

        // 7. Animations- und Durchflussklassen auf Leitungen übertragen
        if (rohrWw) {
            rohrWw.classList.toggle('p-blue', istWwAktiv);
            rohrWw.classList.toggle('pulse', istWwAktiv);
        }
        if (pfeilWw) {
            pfeilWw.classList.toggle('p-blue', istWwAktiv);
        }
    }
}
