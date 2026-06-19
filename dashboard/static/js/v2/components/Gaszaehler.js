// components/Gaszaehler.js
export class Gaszaehler {
    render() {
        return `
            <g id="comp-gas">
                <rect id="box-gas" x="100" y="0" width="140" height="72" class="bx" />

                <!-- Modernes Gas/Flame Icon -->
                <g class="icon-svg" transform="translate(112, 8)">
                    <path d="M12 2c0 4.2-3.8 5.5-3.8 9.5c0 3.3 2.7 6 6 6s6-2.7 6-6c0-4-4.2-5.7-4.2-9.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M11 13.5c.5-1.5 2.5-2.5 2.5-4c0 1.5.5 2.5 2 3c-1.5 .5-2 1.5-2 2.5c0-1-.5-1.5-2.5-1.5z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                </g>

                <text x="142" y="20" class="sv">Gaszähler</text>
                <circle id="dot-gas" cx="225" cy="14" r="4" fill="#64748b"/>
                <text id="gas-gesamt" x="170" y="40" text-anchor="middle" class="su">0,0 m³ · Aus</text>
                <text id="gas-heute" x="170" y="60" text-anchor="middle" class="sl">Heute 0,00 m³</text>
                <line x1="170" y1="72" x2="170" y2="85" class="pipe" />
            </g>
        `;
    }

    /**
     * Aktualisiert die Gaszähler-Anzeige im SVG basierend auf der data.json
     * @param {boolean} aktiv - Wird von der Schema-Hauptklasse übergeben
     * @param {Object} data - Das rohe Server-JSON Objekt
     * @param {SVGElement} svg - Die Referenz auf das übergeordnete SVG-Element
     */
    set(aktiv, data = {}, svg) {
        if (!svg) return;

        const box = svg.querySelector('#box-gas');
        const textGesamt = svg.querySelector('#gas-gesamt');
        const textHeute = svg.querySelector('#gas-heute');
        const comp = svg.querySelector('#comp-gas');

        // Hilfsfunktion zur Formatierung nach deutscher Ländernorm (Komma statt Punkt)
        const formatNum = (val, dec = 2) => val !== undefined && val !== null ? val.toFixed(dec).replace('.', ',') : '--';

        // 1. Daten aus der echten JSON-Struktur extrahieren
        const gesamtStand = data.gas?.display_m3 ?? 32421.936;
        const heuteVerbrauch = data.today?.gas_m3 ?? 0.00;

        // Der Zähler meldet "Ein", wenn die Heizung/Warmwasser läuft UND der Brenner aktiv Flamme hat
        const istBrennerAktiv = data.boiler?.burner_active || aktiv || false;

        // 2. DOM-Inhalte aktualisieren
        if (textGesamt) {
            textGesamt.textContent = `${formatNum(gesamtStand, 3)} m³ · ${istBrennerAktiv ? 'Ein' : 'Aus'}`;
        }

        if (textHeute) {
            textHeute.textContent = `Heute ${formatNum(heuteVerbrauch, 3)} m³`;
        }

        // 3. Visuelle Statusklassen und Theme-Farben toggeln
        if (box) {
            box.classList.toggle('active-gas', istBrennerAktiv);
        }

        // Das Icon färbt sich über 'currentColor' automatisch mit dem Text um!
        // Gelb (var(--yellow) / #eab308) bei aktivem Bezug, sonst gedimmtes Text-Weiß (var(--text) / #e2e8f0)
        if (comp) {
            comp.style.color = istBrennerAktiv ? 'var(--yellow, #eab308)' : 'var(--text, #e2e8f0)';
        }

        // Status-Punkt aktualisieren
        const dot = svg.querySelector('#dot-gas');
        if (dot) dot.setAttribute('fill', istBrennerAktiv ? '#10b981' : '#64748b');
    }
}
