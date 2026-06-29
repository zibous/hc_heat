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

        // Heizperioden (01.09. – 31.08.) dynamisch generieren
        const now = new Date();
        const curYear = now.getFullYear();
        const curMonth = now.getMonth() + 1; // 1-12
        // Aktuelle Heizperiode: wenn >= September → dieses Jahr, sonst Vorjahr
        const hpStartYear = curMonth >= 9 ? curYear : curYear - 1;
        const hpOpts = [];
        for (let y = hpStartYear; y >= hpStartYear - 2; y--) {
            const from = `${y}-09-01`;
            const to = `${y + 1}-08-31`;
            const label = `HP ${y}/${String(y + 1).slice(2)}`;
            const val = `hp:${from}:${to}`;
            hpOpts.push(`<option value="${val}"${saved === val ? ' selected' : ''}>${label}</option>`);
        }

        return `
        <div class="tile tile-daily" style="margin-bottom: 24px; padding: 16px;">
            <div class="tile-head" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="tile-head-lbl">Energiebilanz & Verbrauchshistorie</span>
                    <span class="tile-head-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10M12 20V4M6 20v-6M3 20h18"/></svg></span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span style="font-size:.72rem;color:var(--text-muted);text-transform:uppercase;font-weight:600">Zeitraum</span>
                    <select id="daily-period" style="background:var(--surface);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;">
                        ${opts}
                        <optgroup label="Heizperioden">
                            ${hpOpts.join('')}
                        </optgroup>
                        <option value="custom"${saved === 'custom' ? ' selected' : ''}>Von – Bis</option>
                    </select>
                    <span id="daily-custom-range" style="display:none;align-items:center;gap:4px;">
                        <input type="date" id="daily-from" style="background:var(--surface);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:6px;font-size:.75rem;">
                        <span style="color:var(--text-muted);font-size:.75rem;">–</span>
                        <input type="date" id="daily-to" style="background:var(--surface);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:6px;font-size:.75rem;">
                        <button id="daily-range-go" style="background:var(--accent,#3b82f6);color:#fff;border:none;padding:4px 10px;border-radius:6px;font-size:.75rem;font-weight:600;cursor:pointer;">OK</button>
                    </span>
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
        const customRange = container.querySelector('#daily-custom-range');
        if (periodSel && !periodSel._bound) {
            periodSel._bound = true;
            periodSel.addEventListener('change', async () => {
                const val = periodSel.value;
                localStorage.setItem('heat-daily-period', val);

                // Custom-Range ein-/ausblenden
                if (customRange) customRange.style.display = val === 'custom' ? 'flex' : 'none';
                if (val === 'custom') return; // Warten auf OK-Klick

                try {
                    let url;
                    if (val.startsWith('hp:')) {
                        // Heizperiode: hp:YYYY-MM-DD:YYYY-MM-DD
                        const [, from, to] = val.split(':');
                        url = `${this.basePath}/api/daily?from=${from}&to=${to}`;
                    } else {
                        url = `${this.basePath}/api/daily?days=${val}`;
                    }
                    const res = await fetch(url);
                    if (!res.ok) return;
                    const json = await res.json();
                    if (json && json.data) {
                        const colors = this._getColors();
                        const gasPrice = 0.103;
                        this.updateChart(json.data, colors, gasPrice, container);
                    }
                } catch (e) { console.error('Daily fetch error:', e); }
            });
        }

        // Custom-Range OK-Button
        const rangeGoBtn = container.querySelector('#daily-range-go');
        if (rangeGoBtn && !rangeGoBtn._bound) {
            rangeGoBtn._bound = true;
            rangeGoBtn.addEventListener('click', async () => {
                const from = container.querySelector('#daily-from')?.value;
                const to = container.querySelector('#daily-to')?.value;
                if (!from || !to) return;
                try {
                    const res = await fetch(`${this.basePath}/api/daily?from=${from}&to=${to}`);
                    if (!res.ok) return;
                    const json = await res.json();
                    if (json && json.data) {
                        const colors = this._getColors();
                        const gasPrice = 0.103;
                        this.updateChart(json.data, colors, gasPrice, container);
                    }
                } catch (e) { console.error('Daily range fetch error:', e); }
            });
        }

        // Initial: Custom-Range anzeigen falls gespeichert
        if (customRange && localStorage.getItem('heat-daily-period') === 'custom') {
            customRange.style.display = 'flex';
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

            // 2. Desinfektions- und reine Warmwasseranteile (vom Backend geliefert)
            const disData = dailyData.map(d => d.disinfection_kwh || 0);
            const wwOnly = dailyData.map(d => d.dhw_kwh || 0);

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

        const sumWW = sumD;
        const days = dailyData.length;

        const F = (v, dec = 1) => typeof v === 'number' ? v.toFixed(dec).replace('.', ',') : v;
        const fH = (m) => {
            const h = Math.floor(m / 60);
            const remMin = Math.round(m % 60);
            return h > 0 ? `${h}h ${remMin}m` : `${remMin}m`;
        };

        const badge = (value, label, color = 'var(--text)') =>
            `<div style="display:flex;flex-direction:column;align-items:center;padding:8px 14px;border:1px solid var(--border);border-radius:10px;background:var(--surface);min-width:90px;">
                <span style="font-size:1.1rem;font-weight:700;color:${color};line-height:1.2;">${value}</span>
                <span style="font-size:.65rem;color:var(--text-muted);margin-top:2px;white-space:nowrap;">${label}</span>
            </div>`;

        let html = `<div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding:10px 0;">`;
        html += badge(F(sumE, 1), 'Gesamt kWh', '#6366f1');
        html += badge(F(sumH, 1), 'Heizung kWh', '#ef4444');
        html += badge(F(sumWW, 1), 'Warmwasser kWh', '#3b82f6');
        if (sumDis > 0) html += badge(F(sumDis, 1), 'Desinfektion kWh', '#f59e0b');
        html += badge(F(sumG, 2), 'Gas m³', '#f59e0b');
        html += badge(F(sumE * gpk, 2) + ' €', 'Kosten', '#10b981');
        html += badge(fH(sumB), 'Brennerlaufzeit', 'var(--text)');
        if (days > 1) {
            const unit = days > 90 ? 'Monat' : 'Tag';
            html += badge(F(sumE / days, 1), `⌀ kWh/${unit}`, 'var(--text-muted)');
        }
        html += `</div>`;

        sumTable.innerHTML = html;
    }
}
