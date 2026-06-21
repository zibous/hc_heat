// components/HeizungDailyChart.js

export class HeizungDailyChart {
    constructor() {
        this.dailyChartInstance = null;
        this.basePath = window._bp || '.'; // Übernimmt den globalen Basepath-Fallback
    }

    /**
     * Erzeugt das HTML-Gerüst inklusive Steuerelementen und CSV-Export-Button
     */
    render() {
        const saved = localStorage.getItem('heat-daily-period') || '14';
        const opts = [
            ['1', 'Heute'], ['7', '7 Tage'], ['14', '14 Tage'],
            ['30', '30 Tage'], ['90', '3 Monate'], ['365', 'Jahr']
        ].map(([v, l]) => `<option value="${v}"${v === saved ? ' selected' : ''}>${l}</option>`).join('');

        return `
        <div class="tile tile-daily" style="margin-bottom: 24px; padding: 16px;">
            <div class="tile-head" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="tile-head-lbl">Energiebilanz & Verbrauchshistorie</span>
                    <span class="tile-head-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10M12 20V4M6 20v-6M3 20h18"/></svg></span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:.72rem;color:var(--text-muted);text-transform:uppercase;font-weight:600">Zeitraum</span>
                    <select id="daily-period" style="background:var(--surface);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;">
                        ${opts}
                    </select>
                </div>
            </div>

            <!-- Das Diagramm -->
            <div style="position: relative; width: 100%; height: 360px; margin-bottom: 12px;">
                <canvas id="dailyChart"></canvas>
            </div>

            <!-- Dynamische Text-Zusammenfassung -->
            <div id="daily-summary-table" style="font-size: 0.78rem; color: var(--text-muted); border-top: 1px solid var(--border); padding-top: 10px;"></div>

            <!-- CSV Export unten rechts -->
            <div style="display:flex;justify-content:flex-end;margin-top:10px;">
                <button id="btn-csv-export" style="border: 1px solid var(--border); cursor: pointer; font-family: inherit; background: var(--surface); color: var(--text); padding: 8px 16px; border-radius: 8px; font-size: .78rem; font-weight: 600;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:text-bottom;margin-right:4px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>CSV
                </button>
            </div>
        </div>
        `;
    }

    /**
     * Bindet den CSV-Export-Eventlistener an den Button, sobald das HTML im DOM existiert
     * @param {HTMLElement} container - Das Dashboard-Haupt-HTML Element
     */
    initEvents(container) {
        const exportBtn = container.querySelector('#btn-csv-export');
        if (exportBtn && !exportBtn._bound) {
            exportBtn._bound = true;
            exportBtn.addEventListener('click', () => {
                const days = container.querySelector('#daily-period')?.value || 14;
                window.location.href = `${this.basePath}/api/export?days=${days}`;
            });
        }

        // Period-Selector: Bei Änderung neue Daten laden
        const periodSel = container.querySelector('#daily-period');
        if (periodSel && !periodSel._bound) {
            periodSel._bound = true;
            periodSel.addEventListener('change', async () => {
                const days = periodSel.value;
                localStorage.setItem('heat-daily-period', days);
                try {
                    const res = await fetch(`${this.basePath}/api/daily?days=${days}`);
                    if (!res.ok) return;
                    const json = await res.json();
                    if (json && json.data) {
                        const colors = this._getColors();
                        const gasPrice = 0.103; // Fallback
                        this.updateChart(json.data, colors, gasPrice, container);
                    }
                } catch (e) { console.error('Daily fetch error:', e); }
            });
        }
    }

    _getColors() {
        const s = getComputedStyle(document.documentElement);
        return {
            text: s.getPropertyValue('--text').trim() || '#e2e8f0',
            muted: s.getPropertyValue('--text-muted').trim() || '#8892a4',
            grid: s.getPropertyValue('--border').trim() || '#2e3350'
        };
    }

    /**
     * Wird zyklisch oder nach Zeitraum-Wechsel getriggert, um das Diagramm zu zeichnen
     * @param {Array} dailyData - Das Datenarray aus der API /api/daily
     * @param {Object} colors - Die zentralen Theme-Farben aus der Hauptklasse
     * @param {number} gasPriceKwh - Der geladene Gaspreis (gpk) aus der Config
     * @param {HTMLElement} container - Das Dashboard-Haupt-HTML Element
     */
    updateChart(dailyData, colors, gasPriceKwh = 0.103, container) {
        if (!container || !dailyData || dailyData.length === 0) return;

        const canvas = container.querySelector('#dailyChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        try {
            // 1. Label-Generierung (Formatiert Datum zu MM/JJ oder DD.MM)
            const labels = dailyData.map(d => {
                if (d.day.indexOf(':') > -1) return d.day;
                const parts = d.day.split('-');
                return parts.length === 2 ? `${parts[1]}/${parts[0]}` : `${parts[2]}.${parts[1]}`;
            });

            // 2. Berechnung der Desinfektions- und reinen Warmwasseranteile
            const disData = dailyData.map(d => {
                if (d.day.indexOf(':') > -1) return 0;
                const dt = new Date(d.day);
                return (!isNaN(dt.getTime()) && dt.getDay() === 6) ? Math.min(d.dhw_kwh, d.energy_kwh * 0.05) : 0;
            });
            const wwOnly = dailyData.map((d, i) => Math.max(0, d.dhw_kwh - disData[i]));

            // 3. Vorherige Instanz zerstören (Wichtig gegen Flackern beim Hovern)
            if (this.dailyChartInstance) {
                this.dailyChartInstance.destroy();
            }

            // 4. Chart.js Balken- & Liniendiagramm initialisieren
            // @ts-ignore
            this.dailyChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Heizung', data: dailyData.map(d => d.heat_kwh), backgroundColor: 'rgba(239, 68, 68, 0.7)', stack: 'kwh', yAxisID: 'y' },
                        { label: 'Warmwasser', data: wwOnly, backgroundColor: 'rgba(59, 130, 246, 0.7)', stack: 'kwh', yAxisID: 'y' },
                        { label: 'Desinfektion', data: disData, backgroundColor: 'rgba(245, 158, 11, 0.7)', stack: 'kwh', yAxisID: 'y' },
                        { label: 'Gas m³', data: dailyData.map(d => d.gas_m3 || 0), type: 'line', borderColor: '#f59e0b', borderWidth: 2, pointRadius: 2, tension: 0.3, yAxisID: 'y1', fill: false, borderDash: [4, 2] },
                        { label: 'Kosten €', data: dailyData.map(d => Math.round(d.energy_kwh * gasPriceKwh * 100) / 100), type: 'line', borderColor: '#10b981', borderWidth: 2, pointRadius: 3, tension: 0.3, yAxisID: 'y1', fill: false }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: colors.text, font: { size: 11 }, usePointStyle: true } } },
                    scales: {
                        x: { ticks: { color: colors.muted, font: { size: 10 } }, grid: { color: colors.grid }, stacked: true },
                        y: { title: { display: true, text: 'kWh', color: colors.muted }, ticks: { color: colors.muted }, grid: { color: colors.grid }, stacked: true, position: 'left' },
                        y1: { title: { display: true, text: 'm³ / €', color: colors.muted }, ticks: { color: colors.muted }, grid: { display: false }, position: 'right' }
                    }
                }
            });

            // 5. Erzeugung der mathematischen Text-Zusammenfassung (mainTable)
            this._renderSummaryTable(dailyData, disData, gasPriceKwh, container);

        } catch (error) {
            const sumTable = container.querySelector('#daily-summary-table');
            if (sumTable) sumTable.textContent = `Fehler beim Rendern: ${error.message}`;
        }
    }

    /**
     * Interne Berechnung für die mathematische Zusammenfassung am Fuß der Kachel
     */
    _renderSummaryTable(dailyData, disData, gpk, container) {
        const sumTable = container.querySelector('#daily-summary-table');
        if (!sumTable) return;

        let sumE = 0, sumH = 0, sumD = 0, sumG = 0, sumB = 0, sumDis = 0;
        dailyData.forEach((d, i) => {
            sumE += d.energy_kwh || 0;
            sumH += d.heat_kwh || 0;
            sumD += d.dhw_kwh || 0;
            sumG += d.gas_m3 || 0;
            sumB += d.burner_min || 0;
            sumDis += disData[i] || 0;
        });

        const sumWW = sumD - sumDis;
        const days = dailyData.length;

        // Lokale Formatierungshelfer passend zu deiner App
        const F = (v, dec = 1) => typeof v === 'number' ? v.toFixed(dec).replace('.', ',') : v;
        const fH = (m) => {
            const h = Math.floor(m / 60);
            const remMin = Math.round(m % 60);
            return h > 0 ? `${h}h ${remMin}m` : `${remMin}m`;
        };

        const ico = (path, color='currentColor') => `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" style="vertical-align:text-bottom;margin-right:2px">${path}</svg>`;
        const iHouse = ico('<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', '#ef4444');
        const iDrop = ico('<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>', '#3b82f6');
        const iFlame = ico('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14 0-5.5 3.5-7.5 0 0 .5 4 2 5s2.17 2.97 2.17 4.73A5.5 5.5 0 0 1 12 16.5a5.5 5.5 0 0 1-3.5-2z"/>', '#f59e0b');
        const iGas = ico('<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>', '#f59e0b');
        const iCoin = ico('<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>', '#10b981');
        const iClock = ico('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>');

        let html = `<div style="display:flex; flex-wrap:wrap; gap:16px; justify-content:center; padding:4px 0;">`;
        html += `<span>Σ <strong>${F(sumE, 1)}</strong> kWh</span>`;
        html += `<span style="color:#ef4444">${iHouse} ${F(sumH, 1)} kWh</span>`;
        html += `<span style="color:#3b82f6">${iDrop} ${F(sumWW, 1)} kWh</span>`;
        if (sumDis > 0) html += `<span style="color:#f59e0b">${iFlame} ${F(sumDis, 1)} kWh</span>`;
        html += `<span>${iGas} ${F(sumG, 2)} m³</span>`;
        html += `<span style="color:#10b981">${iCoin} ${F(sumE * gpk, 2)} €</span>`;
        html += `<span>${iClock} ${fH(sumB)}</span>`;

        if (days > 1) {
            const unit = days > 90 ? 'Monat' : 'Tag';
            html += `<span style="color:var(--text-muted)">⌀ ${F(sumE / days, 1)} kWh/${unit}</span>`;
        }
        html += `</div>`;

        sumTable.innerHTML = html;
    }
}
