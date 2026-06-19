// components/HeizkurveChart.js

export class HeizkurveChart {
    constructor() {
        this.chartInstance = null;
    }

    render() {
        return `
        <div class="tile" style="padding: 16px; min-height: 340px; display: flex; flex-direction: column;">
            <div class="tile-head" style="margin-bottom: 4px;">
                <span class="tile-head-lbl">Heizkurve & Arbeitspunkte</span>
                <span class="tile-head-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg></span>
            </div>
            <div style="position: relative; flex: 1; min-height: 0;">
                <canvas id="curveChart"></canvas>
            </div>
            <div id="curveInfo" style="font-size: .7rem; color: var(--text-muted); text-align: center; padding-top: 6px; border-top: 1px solid var(--border); margin-top: 8px;"></div>
        </div>
        `;
    }

    updateChart(data, colors, thermostat, container) {
        const canvas = container.querySelector('#curveChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const scatter = [];
        const soll = [];

        data.forEach(p => {
            if (p.outdoor != null && p.flow != null && p.mode === 'heating') scatter.push({ x: p.outdoor, y: p.flow });
            if (p.outdoor != null && p.target_flow != null) soll.push({ x: p.outdoor, y: p.target_flow });
        });

        /* 1. Berechnete Soll-Heizkurve aus Thermostat-Einstellungen */
        const hc1 = thermostat.hc1 || {};
        const designTemp = hc1.designtemp || 45;
        const minFlow = hc1.minflowtemp || 25;
        const maxFlow = hc1.maxflowtemp || 60;
        const summerTemp = hc1.summertemp || 18;
        const minExt = thermostat.minexttemp != null ? thermostat.minexttemp : -10;

        const sollCurve = [];
        if (designTemp > minFlow) {
            for (let t = minExt; t <= summerTemp + 2; t += 1) {
                let vorlauf = (t >= summerTemp)
                    ? minFlow
                    : designTemp + (minFlow - designTemp) * (t - minExt) / (summerTemp - minExt);

                vorlauf = Math.max(minFlow, Math.min(maxFlow, vorlauf));
                sollCurve.push({ x: t, y: Math.round(vorlauf * 10) / 10 });
            }
        }

        /* 2. Soll-Kurve aus History extrahieren & glätten (Bins-Filterung) */
        const sollBins = {};
        soll.forEach(p => {
            const bin = Math.round(p.x * 2) / 2;
            if (!sollBins[bin]) sollBins[bin] = { sum: 0, cnt: 0 };
            sollBins[bin].sum += p.y;
            sollBins[bin].cnt += 1;
        });

        const sollSmooth = Object.keys(sollBins).map(k => ({
            x: parseFloat(k),
            y: Math.round((sollBins[k].sum / sollBins[k].cnt) * 10) / 10
        })).sort((a, b) => a.x - b.x);

        // Filterung der Soll-Kurve auf den aktiven Ist-Bereich (+/- 3°C)
        let sollLine = sollCurve;
        if (sollCurve.length > 0 && scatter.length > 0) {
            const xLo = scatter.reduce((a, p) => Math.min(a, p.x), Infinity) - 3;
            const xHi = scatter.reduce((a, p) => Math.max(a, p.x), -Infinity) + 3;
            sollLine = sollCurve.filter(p => p.x >= xLo && p.x <= xHi);
        } else if (sollCurve.length === 0) {
            sollLine = sollSmooth;
        }

        /* 3. Lineare Trendlinie berechnen (Linear Regression) */
        let trendLine = [];
        if (scatter.length >= 3) {
            const n = scatter.length;
            let sx = 0, sy = 0, sxy = 0, sx2 = 0;
            scatter.forEach(p => { sx += p.x; sy += p.y; sxy += p.x * p.y; sx2 += p.x * p.x; });
            const denom = n * sx2 - sx * sx;
            if (Math.abs(denom) > 0.001) {
                const m = (n * sxy - sx * sy) / denom;
                const b2 = (sy - m * sx) / n;
                const xMin = scatter.reduce((a, p) => Math.min(a, p.x), Infinity);
                const xMax = scatter.reduce((a, p) => Math.max(a, p.x), -Infinity);
                trendLine = [
                    { x: xMin, y: Math.round((m * xMin + b2) * 10) / 10 },
                    { x: xMax, y: Math.round((m * xMax + b2) * 10) / 10 }
                ];
            }
        }

        // Dynamische Anpassung der Punktgrößen und Transparenzen bei großen Datenmengen
        const alpha = scatter.length < 30 ? 0.7 : scatter.length < 200 ? 0.4 : 0.25;
        const ptSize = scatter.length < 30 ? 4 : scatter.length < 200 ? 3 : 2;
        const allPts = scatter.concat(sollLine);

        // Achsenskalierung berechnen
        const axMinX = allPts.length ? Math.floor(allPts.reduce((a, p) => Math.min(a, p.x), Infinity) - 1) : -10;
        const axMaxX = allPts.length ? Math.ceil(allPts.reduce((a, p) => Math.max(a, p.x), -Infinity) + 1) : 25;
        const axMinY = allPts.length ? Math.floor(allPts.reduce((a, p) => Math.min(a, p.y), Infinity) - 2) : 20;
        const axMaxY = allPts.length ? Math.ceil(allPts.reduce((a, p) => Math.max(a, p.y), -Infinity) + 2) : 55;

        // Datasets zusammenstellen
        const datasets = [
            { label: 'Vorlauf (Heizbetrieb)', data: scatter, backgroundColor: `rgba(239, 68, 68, ${alpha})`, pointRadius: ptSize, order: 2 },
            { label: 'Soll (Heizkurve)', data: sollLine, type: 'line', borderColor: '#10b981', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, order: 1 }
        ];

        if (trendLine.length === 2) {
            datasets.push({ label: 'Trend (Ist)', data: trendLine, type: 'line', borderColor: 'rgba(251, 191, 36, 0.7)', borderWidth: 2, borderDash:[5,3], pointRadius: 0, fill: false, order: 0 });
        }

        if (this.chartInstance) this.chartInstance.destroy();

        // Formatierungs-Hilfsfunktion für Tooltips
        const F = (val) => typeof val === 'number' ? val.toFixed(1).replace('.', ',') : val;

        // @ts-ignore
        this.chartInstance = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: colors.text, font: { size: 11 } } },
                    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${F(ctx.parsed.x)}°C → ${F(ctx.parsed.y)}°C` } }
                },
                scales: {
                    x: { min: axMinX, max: axMaxX, title: { display: true, text: 'Außentemperatur °C', color: colors.muted }, ticks: { color: colors.muted, stepSize: 2 }, grid: { color: colors.grid } },
                    y: { min: axMinY, max: axMaxY, title: { display: true, text: 'Vorlauftemperatur °C', color: colors.muted }, ticks: { color: colors.muted }, grid: { color: colors.grid } }
                }
            }
        });

        // Info-Text unter dem Header aktualisieren
        const curveInfo = container.querySelector('#curveInfo');
        if (curveInfo) {
            if (scatter.length > 0) {
                const oMin = scatter.reduce((a, p) => Math.min(a, p.x), Infinity);
                const oMax = scatter.reduce((a, p) => Math.max(a, p.x), -Infinity);
                curveInfo.textContent = `${scatter.length} Heizpunkte aufgezeichnet (Spektrum: ${F(oMin)}°C bis ${F(oMax)}°C)`;
            } else {
                // Prüfe ob Sommerbetrieb (kein Heizbedarf)
                const summerMode = thermostat?.hc1?.summermode || '';
                const outdoorTemp = data[data.length - 1]?.outdoor || 0;
                if (summerMode === 'Sommer' || outdoorTemp > 18) {
                    curveInfo.innerHTML = `<strong>Sommerbetrieb</strong><br><span style="opacity:.7"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:3px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2"/></svg>Kein Heizbetrieb – Außentemperatur über Heizgrenze. Heizpunkte werden im Winter gesammelt.</span>`;
                } else {
                    curveInfo.innerHTML = `<strong>0 Heizpunkte</strong><br><span style="opacity:.7"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:text-bottom;margin-right:3px"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>Noch wenige Heizpunkte. Die grüne Linie zeigt die eingestellte Heizkurve: Je kälter draußen, desto wärmer der Vorlauf.</span>`;
                }
            }
        }
    }
}
