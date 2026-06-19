// components/Therme.js
export class Therme {
    render() {
        return `
            <g id="comp-therme" transform="translate(0, 15)">
                <rect id="box-therme" x="80" y="75" width="180" height="140" class="bx" />
                <text x="170" y="97" text-anchor="middle" class="sv">GB172-14</text>
                <circle id="dot-therme" cx="248" cy="87" r="4" fill="#64748b"/>

                <!-- Dynamische Status-Zeile mit der neuen, schöneren Vektor-Flamme -->
                <g id="therme-status-group">
                    <!-- Das Icon wird skaliert (scale(0.8)) und über JS exakt positioniert -->
                    <g id="therme-icon-container" transform="translate(112, 100) scale(0.8)">
                        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 3.5z"
                              fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </g>
                    <text id="therme-status" x="140" y="114" class="st">Aus</text>
                </g>

                <text id="therme-werte" x="170" y="130" text-anchor="middle" class="su">Vorlauf --°C · Soll --°C</text>
                <text id="therme-pumpe" x="170" y="146" text-anchor="middle" class="su">Pumpe Aus</text>

                <rect x="95" y="155" width="150" height="4" rx="2" class="bg-bar" />
                <rect id="bar-therme-brand" x="95" y="155" width="0" height="4" rx="2" class="p-red" />
                <rect x="95" y="163" width="150" height="4" rx="2" class="bg-bar" />
                <rect id="bar-therme-mod" x="95" y="163" width="0" height="4" rx="2" class="p-green" />

                <line x1="170" y1="205" x2="170" y2="220" class="pipe" />
                <line id="rohr-vorlauf" x1="260" y1="110" x2="470" y2="110" class="pipe" />
                <line id="rohr-ruecklauf" x1="260" y1="160" x2="470" y2="160" class="pipe" />
                <polygon id="pfeil-vorlauf" points="465,105 475,110 465,115" class="bg-bar" />
                <polygon id="pfeil-ruecklauf" points="265,155 255,160 265,165" class="bg-bar" />
                <text x="390" y="102" class="sl">Vorlauf</text>
                <text x="390" y="176" class="sl">Rücklauf</text>
            </g>
        `;
    }

    /**
     * Aktualisiert den Kessel-Status im SVG basierend auf der data.json
     * @param {boolean} aktiv - Fallback-Zustand von der übergeordneten Steuerung
     * @param {number} modulation - Fallback-Modulationswert von der übergeordneten Steuerung
     * @param {Object} data - Das rohe Server-JSON Objekt
     * @param {SVGElement} svg - Die Referenz auf das übergeordnete SVG-Element
     */
    set(aktiv, modulation = 0, data = {}, svg) {
        if (!svg) return;

        const box = svg.querySelector('#box-therme');
        const statusText = svg.querySelector('#therme-status');
        const statusGroup = svg.querySelector('#therme-status-group');
        const iconContainer = svg.querySelector('#therme-icon-container');
        const werteText = svg.querySelector('#therme-werte');
        const pumpeText = svg.querySelector('#therme-pumpe');
        const modBalken = svg.querySelector('#bar-therme-mod');
        const brandBalken = svg.querySelector('#bar-therme-brand');

        // Hilfsfunktion zur Formatierung nach deutscher Ländernorm (Komma statt Punkt)
        const formatNum = (val, dec = 1) => val !== undefined && val !== null ? val.toFixed(dec).replace('.', ',') : '--';

        // 1. Datenpfade direkt aus dem data.json Kessel-Objekt auslesen
        const b = data.boiler || {};
        const istBrennerAktiv = b.burner_active ?? aktiv ?? false;
        const aktuelleModulation = b.burner_power_percent ?? modulation ?? 0;
        const istPumpeAktiv = b.pump_active || (b.pump_modulation > 0);

        // 2. Dynamische, optische Zentrierung basierend auf dem Zustand
        if (statusText && iconContainer) {
            if (istBrennerAktiv) {
                statusText.textContent = 'Heizt';
                iconContainer.setAttribute('transform', 'translate(108, 98) scale(0.8)');
                statusText.setAttribute('x', '138');
            } else {
                statusText.textContent = 'Aus';
                iconContainer.setAttribute('transform', 'translate(116, 98) scale(0.8)');
                statusText.setAttribute('x', '146');
            }
        }

        // 3. Semantische Farb-Zuweisung (Rot bei Heizbetrieb, sonst Standard-Theme-Weiß)
        if (statusGroup) {
            statusGroup.style.color = istBrennerAktiv ? 'var(--red, #ef4444)' : 'var(--text, #e2e8f0)';
        }
        if (statusText) {
            statusText.style.fill = istBrennerAktiv ? 'var(--red, #ef4444)' : '';
        }

        // Status-Punkt
        const dot = svg.querySelector('#dot-therme');
        if (dot) dot.setAttribute('fill', istBrennerAktiv ? '#10b981' : '#64748b');

        // 4. Pumpenstatus textuell aktualisieren (Mit Modulationsanzeige der Kesselpumpe)
        if (pumpeText) {
            pumpeText.textContent = istPumpeAktiv
                ? `Pumpe Ein (${b.pump_modulation || 0}%)`
                : 'Pumpe Aus';
        }

        // 5. Temperaturen formatieren und einpflegen
        if (werteText) {
            const vTemp = b.flow_temp ?? '--';
            const sTemp = b.flow_set_temp ?? '--';
            werteText.textContent = `Vorlauf ${formatNum(vTemp)}°C · Soll ${formatNum(sTemp)}°C`;
        }

        // 6. Balkenanzeigen skalieren (Brand = Ein/Aus, Mod = Modulationsfortschritt 0-150px)
        if (brandBalken) {
            brandBalken.setAttribute('width', istBrennerAktiv ? '150' : '0');
        }
        if (modBalken) {
            const balkenBreite = (aktuelleModulation / 100) * 150;
            modBalken.setAttribute('width', istBrennerAktiv ? balkenBreite.toString() : '0');
        }

        // 7. Geerbtes CSS-Klassentoggling für den Glow-Effekt des Kessels
        if (box) {
            box.classList.toggle('active-therme', istBrennerAktiv);
        }
    }
}
