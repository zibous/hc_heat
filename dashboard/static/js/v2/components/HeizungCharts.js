// components/HeizungCharts.js
import { HeizkurveChart } from './chart/HeizkurveChart.js';
import { HeizungDailyChart } from './chart/HeizungDailyChart.js';

export class HeizungCharts {
    constructor() {
        this.tempChartInstance = null;
        this.heizkurve = new HeizkurveChart();
        this.dailyChart = new HeizungDailyChart();
    }

    render() {
        return `
        <div class="section-title" style="margin: 2rem 0 1rem 0; font-size: 1.1rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Historische Verläufe</div>

        <div class="tiles-grid" style="grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); margin-bottom: 24px; align-items: stretch;">
            <!-- 1. Temperaturverlauf -->
            <div class="tile" style="padding: 16px; min-height: 460px; display: flex; flex-direction: column;">
                <div class="tile-head" style="margin-bottom: 12px;">
                    <span class="tile-head-lbl">Temperaturverlauf (24h)</span>
                    <span class="tile-head-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m18.7 8-5.1 5.2-2.8-2.7L7 14.3"/></svg></span>
                </div>
                <div style="position: relative; flex: 1; min-height: 0;">
                    <canvas id="tempChart"></canvas>
                </div>
                <div id="temp-summary" style="font-size:.72rem;color:var(--text-muted);text-align:center;padding-top:6px;border-top:1px solid var(--border);margin-top:8px;"></div>
            </div>

            <!-- 2. Heizkurve -->
            ${this.heizkurve.render()}
        </div>

        <!-- 3. Das neue Tagesverlauf & Energie-Diagramm (Nutzt volle Zeilenbreite) -->
        ${this.dailyChart.render()}

        <div id="summary-wrapper"></div>
        `;
    }

    update(data, container) {
        if (!container || !data) return;

        // 1. ABSICHERUNG: Holt die Arrays oder setzt sie auf null
        const hist = data.history || data.verbrauchHeute?.verlaufsDaten || null;
        const dailyHistoryData = data.daily_history || null;
        const thermostat = data.thermostat || {};

        // Verlässt die Funktion geräuschlos, wenn im API-JSON keine Historie mitskaliert wird
        if (!hist || !Array.isArray(hist) || hist.length < 2) {
            console.warn("HeizungCharts: Keine historischen Datenreihen im JSON. Überspringe Diagramm-Render.");
            return;
        }

        // Registriere die Klick-Events für den Export-Button einmalig beim Update
        this.dailyChart.initEvents(container);

        const colors = this._getThemeColors();
        const sampledData = this._downsample(hist, 500);

        // Temperaturverlauf-Canvas rendern
        const canvas = container.querySelector('#tempChart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            if (this.tempChartInstance) this.tempChartInstance.destroy();

            const labels = sampledData.map(p => {
                const d = new Date(p.ts);
                return `${d.getDate().toString().padStart(2, '0')}. ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
            });

            // @ts-ignore
            this.tempChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Außen', data: sampledData.map(p => p.outdoor), borderColor: '#3b82f6', borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
                        { label: 'Vorlauf', data: sampledData.map(p => p.flow), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
                        { label: 'Vorlauf Soll', data: sampledData.map(p => p.target_flow || p.flow_set), borderColor: '#10b981', borderWidth: 1.5, borderDash:[5,3], pointRadius: 0, tension: 0.3 },
                        { label: 'Warmwasser', data: sampledData.map(p => p.dhw), borderColor: '#f59e0b', borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
                        { label: 'WW Soll', data: sampledData.map(p => p.dhw_set), borderColor: '#f59e0b', borderWidth: 1, borderDash:[4,2], pointRadius: 0, tension: 0.3 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: colors.text, font: { size: 11 }, usePointStyle: true, pointStyle: 'line' } } },
                    scales: {
                        x: { ticks: { color: colors.muted, font: { size: 10 } }, grid: { color: colors.grid } },
                        y: { ticks: { color: colors.muted, font: { size: 10 } }, grid: { color: colors.grid } }
                    }
                }
            });
        }

        // Temperatur-KPI-Summary mit SVG-Icons
        const summaryEl = container.querySelector('#temp-summary');
        if (summaryEl && sampledData.length > 0) {
            const outdoors = sampledData.map(p => p.outdoor).filter(v => v != null);
            const dhws = sampledData.map(p => p.dhw).filter(v => v != null);
            const oMin = Math.min(...outdoors).toFixed(1);
            const oMax = Math.max(...outdoors).toFixed(1);
            const oAvg = (outdoors.reduce((a, b) => a + b, 0) / outdoors.length).toFixed(1);
            const wMin = Math.min(...dhws).toFixed(1);
            const wMax = Math.max(...dhws).toFixed(1);
            const iconSun = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:2px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
            const iconDrop = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:2px"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>';
            summaryEl.innerHTML = `${iconSun} Außen ${oMin}–${oMax}°C (⌀ ${oAvg}°C) &nbsp;·&nbsp; ${iconDrop} WW ${wMin}–${wMax}°C`;
        }

        // Updates an das Heizkurven-Submodul weitergeben
        this.heizkurve.updateChart(sampledData, colors, thermostat, container);

        // 2. ABSICHERUNG: Tagesverlauf-Chart-Render nur triggern, wenn Daten existieren
        if (dailyHistoryData && Array.isArray(dailyHistoryData) && dailyHistoryData.length > 0) {
            const gasPrice = data.costs?.gas_price_kwh || 0.103;
            this.dailyChart.updateChart(dailyHistoryData, colors, gasPrice, container);
        }
    }

    _downsample(arr, maxPts) {
        if (!arr || arr.length <= maxPts) return arr;
        const step = Math.ceil(arr.length / maxPts), out = [];
        for (let i = 0; i < arr.length; i += step) out.push(arr[i]);
        if (out[out.length - 1] !== arr[arr.length - 1]) out.push(arr[arr.length - 1]);
        return out;
    }

    _getThemeColors() {
        const style = getComputedStyle(document.documentElement);
        return {
            text: style.getPropertyValue('--text').trim() || '#e2e8f0',
            muted: style.getPropertyValue('--text-muted').trim() || '#8892a4',
            grid: style.getPropertyValue('--border').trim() || '#2e3350'
        };
    }
}
