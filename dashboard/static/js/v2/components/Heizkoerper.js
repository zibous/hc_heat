// components/Heizkoerper.js
export class Heizkoerper {
    render() {
        return `
            <g id="comp-hk">
                <rect id="box-hk" x="480" y="75" width="250" height="150" class="bx" />

                <!-- Modernes Heizkörper Icon -->
                <g class="icon-svg" transform="translate(500, 86)">
                    <rect x="2" y="4" width="20" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="2"/>
                    <line x1="6" y1="4" x2="6" y2="20" stroke="currentColor" stroke-width="2"/>
                    <line x1="10" y1="4" x2="10" y2="20" stroke="currentColor" stroke-width="2"/>
                    <line x1="14" y1="4" x2="14" y2="20" stroke="currentColor" stroke-width="2"/>
                    <line x1="18" y1="4" x2="18" y2="20" stroke="currentColor" stroke-width="2"/>
                </g>

                <text x="530" y="101" class="sv">Heizkörper</text>
                <circle id="dot-hk" cx="715" cy="91" r="4" fill="#64748b"/>
                <text id="hk-status" x="605" y="118" text-anchor="middle" class="st">Aus</text>
                <text id="hk-werte" x="605" y="134" text-anchor="middle" class="su">Vorlauf --°C</text>
                <rect x="510" y="142" width="190" height="4" rx="2" class="bg-bar" />
                <rect id="bar-hk" x="510" y="142" width="0" height="4" rx="2" class="p-red" />
            </g>
        `;
    }

    /**
     * Aktualisiert die Heizkörper-Anzeige im SVG basierend auf der data.json
     * @param {boolean} aktiv - Vorsteuerungs-Flag der Hauptkomponente
     * @param {Object} data - Das rohe Server-JSON Objekt
     * @param {SVGElement} svg - Die Referenz auf das übergeordnete SVG-Element
     */
    set(aktiv, data = {}, svg) {
        if (!svg) return;

        const box = svg.querySelector('#box-hk');
        const statusText = svg.querySelector('#hk-status');
        const werteText = svg.querySelector('#hk-werte');
        const comp = svg.querySelector('#comp-hk');
        const rohrVorlauf = svg.querySelector('#rohr-vorlauf');
        const rohrRuecklauf = svg.querySelector('#rohr-ruecklauf');
        const pfeilVorlauf = svg.querySelector('#pfeil-vorlauf');
        const pfeilRuecklauf = svg.querySelector('#pfeil-ruecklauf');
        const hkBalken = svg.querySelector('#bar-hk');

        // Hilfsfunktion zur Formatierung nach deutscher Ländernorm (Komma statt Punkt)
        const formatNum = (val, dec = 1) => val !== undefined && val !== null ? val.toFixed(dec).replace('.', ',') : '--';

        // 1. Datenpfade aus der echten JSON-Struktur auslesen
        const hc = data.heating_circuit || {};
        const vTemp = hc.flow_temp ?? data.boiler?.flow_temp ?? null;

        // Heizkreis ist aktiv wenn das Flag gesetzt ist ODER die Heizkreispumpe läuft ODER der Modus "heating" ist
        const istHeizkreisAktiv = aktiv || hc.pump_active || data.mode === 'heating';

        // 2. DOM-Inhalte aktualisieren
        if (statusText) {
            statusText.textContent = istHeizkreisAktiv ? 'Ein' : 'Aus';
        }

        if (werteText) {
            werteText.textContent = `Vorlauf ${formatNum(vTemp)}°C`;
        }

        if (hkBalken) {
            hkBalken.setAttribute('width', istHeizkreisAktiv ? '190' : '0');
        }

        // 3. Visuelle Statusklassen und Theme-Farben toggeln
        if (box) {
            box.classList.toggle('active-hk', istHeizkreisAktiv);
        }

        if (comp) {
            comp.style.color = istHeizkreisAktiv ? 'var(--red, #ef4444)' : 'var(--text, #e2e8f0)';
        }

        // Status-Punkt
        const dot = svg.querySelector('#dot-hk');
        if (dot) dot.setAttribute('fill', istHeizkreisAktiv ? '#10b981' : '#64748b');

        // 4. Externe Rohrleitungs- und Richtungspfeil-Animationen im Schema mappen
        if (rohrVorlauf) {
            rohrVorlauf.classList.toggle('p-red', istHeizkreisAktiv);
            rohrVorlauf.classList.toggle('pulse', istHeizkreisAktiv);
        }
        if (rohrRuecklauf) {
            rohrRuecklauf.classList.toggle('p-blue', istHeizkreisAktiv);
        }
        if (pfeilVorlauf) {
            pfeilVorlauf.classList.toggle('p-red', istHeizkreisAktiv);
        }
        if (pfeilRuecklauf) {
            pfeilRuecklauf.classList.toggle('p-blue', istHeizkreisAktiv);
        }
    }
}
