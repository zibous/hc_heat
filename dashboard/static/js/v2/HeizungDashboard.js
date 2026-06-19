// HeizungDashboard.js
import { HeizungSchema } from './components/HeizungSchema.js';
import { HeizungStats } from './components/HeizungStats.js';
import { HeizungSettings } from './components/HeizungSettings.js';
import { HeizungCharts } from './components/HeizungCharts.js';

export class HeizungDashboard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.modules = {
            stats: new HeizungStats(),
            schema: new HeizungSchema(),
            charts: new HeizungCharts(),
            settings: new HeizungSettings()
        };

        this.initHTML();
    }

    initHTML() {
        this.container.innerHTML = `
            <!-- Globaler Error-Banner -->
            <div id="error-banner" style="display:none"></div>

            <!-- Statistik-Kacheln -->
            <div id="section-stats"></div>

            <!-- Anlagenschema (Inklusive Footer ganz unten im Schema) -->
            <div id="section-schema"></div>

            <!-- Charts -->
            <div id="section-charts"></div>

            <!-- Einstellungs-Kacheln -->
            <div id="section-settings"></div>
        `;

        document.getElementById('section-stats').innerHTML = this.modules.stats.render();
        document.getElementById('section-schema').innerHTML = this.modules.schema.render();
        document.getElementById('section-charts').innerHTML = this.modules.charts.render();
        document.getElementById('section-settings').innerHTML = this.modules.settings.render();

        // Event-Listener sofort registrieren (Period-Selector, CSV-Button)
        this.modules.charts.dailyChart.initEvents(this.container);
    }

    update(jsonRawData) {
        if (!jsonRawData) return;

        this._updateErrorBanner(jsonRawData);
        this.modules.stats.update(jsonRawData, this.container);
        this.modules.schema.update(jsonRawData, this.container);
        this.modules.charts.update(jsonRawData, this.container);
        this.modules.settings.update(jsonRawData, this.container);
    }

    _updateErrorBanner(data) {
        const banner = this.container.querySelector('#error-banner');
        if (!banner) return;

        const errors = data.errors || {};
        const count = errors.count || 0;
        const boilerErr = errors.boiler || {};
        const thermoErr = errors.thermostat || {};

        if (count === 0 && !boilerErr.code && !thermoErr.code) {
            banner.style.display = 'none';
            return;
        }

        let lines = [];
        if (boilerErr.code) {
            lines.push(`<span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:4px"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14 0-5.5 3.5-7.5 0 0 .5 4 2 5s2.17 2.97 2.17 4.73A5.5 5.5 0 0 1 12 16.5a5.5 5.5 0 0 1-3.5-2z"/></svg><strong>Kessel:</strong> ${boilerErr.code} – ${boilerErr.description || ''} (${boilerErr.date || ''})</span>`);
        }
        if (thermoErr.code) {
            lines.push(`<span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:4px"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg><strong>Thermostat:</strong> ${thermoErr.code} – ${thermoErr.description || ''} (${thermoErr.date || ''})</span>`);
        }
        if (!lines.length && count > 0) {
            lines.push(`<span><strong>${count} Fehler</strong> aktiv</span>`);
        }

        banner.style.display = '';
        banner.innerHTML = `
            <div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:10px;padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" style="flex-shrink:0"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <div style="display:flex;flex-direction:column;gap:4px;font-size:.82rem;color:#fca5a5;">
                    ${lines.join('')}
                </div>
            </div>
        `;
    }
}
