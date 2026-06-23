// components/HeizungSchema.js
import { Gaszaehler } from './Gaszaehler.js';
import { Therme } from './Therme.js';
import { Heizkoerper } from './Heizkoerper.js';
import { Warmwasser } from './Warmwasser.js';
import { HeizungStatusFooter } from './HeizungStatusFooter.js'; // NEU

export class HeizungSchema {
    constructor() {
        this.components = {
            gas: new Gaszaehler(),
            therme: new Therme(),
            hk: new Heizkoerper(),
            ww: new Warmwasser()
        };
        // Instanziiere den Footer als Sub-Komponente
        this.statusFooter = new HeizungStatusFooter();
    }

    render() {
        return `
        <div class="tile tile-schema">
            <div class="tile-head">
                <span class="tile-head-lbl">Anlagenschema & Flussdiagramm</span>
                <span class="status-pulse-dot"></span>
            </div>

            <div class="schema-svg-container" style="margin-bottom: 16px;">
                <svg id="heizung-view" viewBox="0 0 760 420" style="width:100%; height:auto; max-height:420px;">
                  <rect x="5" y="145" width="65" height="55" class="bx" />
                  <text x="37" y="168" text-anchor="middle" class="sv" style="font-size:12px">RC310</text>
                  <text x="37" y="184" text-anchor="middle" class="sl" id="rc310-svg-mode">auto</text>
                  <line x1="70" y1="172" x2="80" y2="172" class="pipe" />

                  ${this.components.gas.render()}
                  ${this.components.therme.render()}
                  ${this.components.hk.render()}
                  ${this.components.ww.render()}
                </svg>
            </div>

            <!-- HIER PLATZIERT: Der Footer sitzt nun innerhalb der Schema-Kachel ganz unten -->
            <div style="border-top: 1px solid var(--border); padding-top: 14px; margin-top: 14px;">
                ${this.statusFooter.render()}
            </div>
        </div>
        `;
    }

    update(data, container) {
        if (!container || !data) return;

        const svg = container.querySelector('#heizung-view');
        if (!svg) return;

        const currentMode = data.mode || 'standby';
        const isGasActive = data.boiler?.burner_active || false;
        const isHeatingActive = currentMode === 'heating';
        const isDhwActive = currentMode === 'dhw' || data.dhw?.charging || false;
        const bModulation = data.boiler?.burner_power_percent || 0;

        const rcModeText = svg.querySelector('#rc310-svg-mode');
        if (rcModeText) {
            rcModeText.textContent = data.thermostat?.hc1?.mode || 'auto';
        }

        // 1. Update für die SVG-Anlagenkomponenten
        this.components.gas.set(isGasActive, data, svg);
        this.components.therme.set(isGasActive, bModulation, data, svg);
        this.components.hk.set(isHeatingActive, data, svg);
        this.components.ww.set(isDhwActive, data, svg);

        // 2. Update für den integrierten Status-Footer
        this.statusFooter.update(data, container);
    }
}
