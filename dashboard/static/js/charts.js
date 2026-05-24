/* charts.js – Temperaturverlauf + Heizkurve */
'use strict';

var tempChart = null, curveChart = null;

function downsample(arr, maxPts) {
    if (!arr || arr.length <= maxPts) return arr;
    var step = Math.ceil(arr.length / maxPts), out = [];
    for (var i = 0; i < arr.length; i += step) out.push(arr[i]);
    if (out[out.length - 1] !== arr[arr.length - 1]) out.push(arr[arr.length - 1]);
    return out;
}

function renderCharts(hist, thermostat) {
    if (!hist || hist.length < 2) return;
    var c = cc();
    var data = downsample(hist, 500);
    var labels = data.map(function (p) {
        var d = new Date(p.ts);
        return d.getDate().toString().padStart(2, '0') + '. ' + d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
    });

    /* Temperaturverlauf */
    var ctx1 = document.getElementById('tempChart').getContext('2d');
    if (tempChart) tempChart.destroy();
    tempChart = new Chart(ctx1, {
        type: 'line', data: {
            labels: labels, datasets: [
                { label: 'Außen', data: data.map(function (p) { return p.outdoor }), borderColor: '#3b82f6', borderWidth: 1.5, pointRadius: 0, tension: .3 },
                { label: 'Vorlauf', data: data.map(function (p) { return p.flow }), borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, tension: .3 },
                { label: 'Vorlauf Soll', data: data.map(function (p) { return p.target_flow || p.flow_set }), borderColor: '#ef4444', borderWidth: 1, borderDash: [5, 3], pointRadius: 0, tension: .3 },
                { label: 'Warmwasser', data: data.map(function (p) { return p.dhw }), borderColor: '#f59e0b', borderWidth: 1.5, pointRadius: 0, tension: .3 },
                { label: 'WW Soll', data: data.map(function (p) { return p.dhw_set }), borderColor: '#f59e0b', borderWidth: 1, borderDash: [5, 3], pointRadius: 0, tension: .3 }
            ]
        }, options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { labels: { color: c.text, font: { size: 11 }, usePointStyle: true, pointStyle: 'line' } } },
            scales: { x: { ticks: { color: c.muted, maxTicksLimit: 14, font: { size: 10 } }, grid: { color: c.grid } }, y: { ticks: { color: c.muted, font: { size: 10 } }, grid: { color: c.grid } } }
        }
    });

    /* Heizkurve */
    _renderCurveChart(data, c, thermostat);

    /* Temperaturverlauf Zusammenfassung */
    _renderTempSummary(data);
}

function _renderCurveChart(data, c, thermostat) {
    var scatter = [], soll = [];
    data.forEach(function (p) {
        if (p.outdoor != null && p.flow != null && p.mode === 'heating') scatter.push({ x: p.outdoor, y: p.flow });
        if (p.outdoor != null && p.target_flow != null) soll.push({ x: p.outdoor, y: p.target_flow });
    });

    /* Berechnete Soll-Heizkurve aus Thermostat-Einstellungen */
    var hc1 = thermostat && thermostat.hc1 ? thermostat.hc1 : {};
    var designTemp = hc1.designtemp || 45;   /* Vorlauf bei minexttemp */
    var minFlow = hc1.minflowtemp || 25;     /* Minimum Vorlauf */
    var maxFlow = hc1.maxflowtemp || 60;     /* Maximum Vorlauf */
    var summerTemp = hc1.summertemp || 18;    /* Ab hier Sommerbetrieb */
    var minExt = (thermostat && thermostat.minexttemp != null) ? thermostat.minexttemp : -10;

    /* Lineare Heizkurve: minExt → designTemp, summerTemp → minFlow */
    var sollCurve = [];
    if (designTemp > minFlow) {
        var step = 1;
        for (var t = minExt; t <= summerTemp + 2; t += step) {
            var vorlauf;
            if (t >= summerTemp) {
                vorlauf = minFlow;
            } else {
                vorlauf = designTemp + (minFlow - designTemp) * (t - minExt) / (summerTemp - minExt);
            }
            vorlauf = Math.max(minFlow, Math.min(maxFlow, vorlauf));
            sollCurve.push({ x: t, y: Math.round(vorlauf * 10) / 10 });
        }
    }

    /* Soll-Kurve: berechnete Heizkurve oder Fallback aus History */
    var sollBins = {};
    soll.forEach(function (p) {
        var bin = Math.round(p.x * 2) / 2;
        if (!sollBins[bin]) sollBins[bin] = { sum: 0, cnt: 0 };
        sollBins[bin].sum += p.y; sollBins[bin].cnt += 1;
    });
    var sollSmooth = Object.keys(sollBins).map(function (k) {
        return { x: parseFloat(k), y: Math.round(sollBins[k].sum / sollBins[k].cnt * 10) / 10 };
    }).sort(function (a, b) { return a.x - b.x });
    /* Berechnete Kurve hat Vorrang, Fallback auf History-Daten */
    /* Soll-Kurve nur im Bereich der Ist-Punkte anzeigen (± 3°C) */
    var sollLine;
    if (sollCurve.length > 0 && scatter.length > 0) {
        var xLo = scatter.reduce(function (a, p) { return Math.min(a, p.x) }, Infinity) - 3;
        var xHi = scatter.reduce(function (a, p) { return Math.max(a, p.x) }, -Infinity) + 3;
        sollLine = sollCurve.filter(function (p) { return p.x >= xLo && p.x <= xHi; });
    } else {
        sollLine = sollCurve.length > 0 ? sollCurve : sollSmooth;
    }

    /* Trendlinie */
    var trendLine = [];
    if (scatter.length >= 3) {
        var n = scatter.length, sx = 0, sy = 0, sxy = 0, sx2 = 0;
        scatter.forEach(function (p) { sx += p.x; sy += p.y; sxy += p.x * p.y; sx2 += p.x * p.x });
        var denom = n * sx2 - sx * sx;
        if (Math.abs(denom) > 0.001) {
            var m = (n * sxy - sx * sy) / denom, b2 = (sy - m * sx) / n;
            var xMin = scatter.reduce(function (a, p) { return Math.min(a, p.x) }, Infinity);
            var xMax = scatter.reduce(function (a, p) { return Math.max(a, p.x) }, -Infinity);
            trendLine = [{ x: xMin, y: Math.round((m * xMin + b2) * 10) / 10 }, { x: xMax, y: Math.round((m * xMax + b2) * 10) / 10 }];
        }
    }

    var alpha = scatter.length < 30 ? .7 : scatter.length < 200 ? .4 : .25;
    var ptSize = scatter.length < 30 ? 4 : scatter.length < 200 ? 3 : 2;
    var allPts = scatter.concat(sollLine);
    var axMinX = allPts.length ? Math.floor(allPts.reduce(function (a, p) { return Math.min(a, p.x) }, Infinity) - 1) : -10;
    var axMaxX = allPts.length ? Math.ceil(allPts.reduce(function (a, p) { return Math.max(a, p.x) }, -Infinity) + 1) : 25;
    var axMinY = allPts.length ? Math.floor(allPts.reduce(function (a, p) { return Math.min(a, p.y) }, Infinity) - 2) : 20;
    var axMaxY = allPts.length ? Math.ceil(allPts.reduce(function (a, p) { return Math.max(a, p.y) }, -Infinity) + 2) : 55;

    var ds = [
        { label: 'Vorlauf (Heizbetrieb)', data: scatter, backgroundColor: 'rgba(239,68,68,' + alpha + ')', pointRadius: ptSize, order: 2 },
        { label: 'Soll (Heizkurve)', data: sollLine, type: 'line', borderColor: '#10b981', borderWidth: 2, pointRadius: 0, tension: .3, fill: false, order: 1 }
    ];
    if (trendLine.length === 2) ds.push({ label: 'Trend (Ist)', data: trendLine, type: 'line', borderColor: 'rgba(251,191,36,0.7)', borderWidth: 2, borderDash: [6, 4], pointRadius: 0, fill: false, order: 0 });

    var ctx2 = document.getElementById('curveChart').getContext('2d');
    if (curveChart) curveChart.destroy();
    curveChart = new Chart(ctx2, {
        type: 'scatter', data: { datasets: ds },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { labels: { color: c.text, font: { size: 11 } } }, tooltip: { callbacks: { label: function (ctx) { return ctx.dataset.label + ': ' + F(ctx.parsed.x, 1) + '°C → ' + F(ctx.parsed.y, 1) + '°C' } } } },
            scales: {
                x: { min: axMinX, max: axMaxX, title: { display: true, text: 'Außentemperatur °C', color: c.muted }, ticks: { color: c.muted, stepSize: 2 }, grid: { color: c.grid } },
                y: { min: axMinY, max: axMaxY, title: { display: true, text: 'Vorlauftemperatur °C', color: c.muted }, ticks: { color: c.muted }, grid: { color: c.grid } }
            }
        }
    });

    var curveInfo = document.getElementById('curveInfo');
    if (curveInfo) {
        var info = scatter.length + ' Heizpunkte';
        if (scatter.length > 0) { var oMin = scatter.reduce(function (a, p) { return Math.min(a, p.x) }, Infinity); var oMax = scatter.reduce(function (a, p) { return Math.max(a, p.x) }, -Infinity); info += ' · Außen ' + F(oMin, 1) + '–' + F(oMax, 1) + '°C'; }
        if (trendLine.length === 2) info += ' · Trend: ' + F(trendLine[0].y, 1) + '°C → ' + F(trendLine[1].y, 1) + '°C';
        /* Verständliche Zusammenfassung */
        var summary = '';
        if (scatter.length >= 3 && trendLine.length === 2 && sollCurve.length > 0) {
            /* Vergleich: Ist-Trend vs. Soll-Kurve */
            var midX = Math.round((scatter.reduce(function (a, p) { return a + p.x }, 0) / scatter.length) * 10) / 10;
            var sollAtMid = designTemp + (minFlow - designTemp) * (midX - minExt) / (summerTemp - minExt);
            sollAtMid = Math.max(minFlow, Math.min(maxFlow, sollAtMid));
            var m = (trendLine[1].y - trendLine[0].y) / (trendLine[1].x - trendLine[0].x);
            var istAtMid = trendLine[0].y + m * (midX - trendLine[0].x);
            var diff = istAtMid - sollAtMid;
            if (Math.abs(diff) < 1.5) {
                summary = '✅ Die Heizung arbeitet im Sollbereich. Bei ' + F(midX, 0) + '°C Außentemperatur liegt der Vorlauf nahe am Soll (' + F(sollAtMid, 0) + '°C).';
            } else if (diff > 0) {
                summary = '⚠️ Der Vorlauf liegt ~' + F(Math.abs(diff), 0) + '°C über dem Soll. Bei ' + F(midX, 0) + '°C außen: Ist ' + F(istAtMid, 0) + '°C vs. Soll ' + F(sollAtMid, 0) + '°C. Die Heizung arbeitet wärmer als nötig.';
            } else {
                summary = 'ℹ️ Der Vorlauf liegt ~' + F(Math.abs(diff), 0) + '°C unter dem Soll. Bei ' + F(midX, 0) + '°C außen: Ist ' + F(istAtMid, 0) + '°C vs. Soll ' + F(sollAtMid, 0) + '°C.';
            }
        } else if (scatter.length < 3) {
            summary = 'ℹ️ Noch wenige Heizpunkte. Die grüne Linie zeigt die eingestellte Heizkurve: Je kälter draußen, desto wärmer der Vorlauf.';
        }
        if (summary) info += '\n' + summary;
        curveInfo.innerHTML = info.replace('\n', '<br>');
    }
}


function _renderTempSummary(data) {
    var el = document.getElementById('tempInfo');
    if (!el || !data || data.length < 2) return;

    /* Außentemperatur Min/Max/Durchschnitt */
    var outVals = data.filter(function (p) { return p.outdoor != null }).map(function (p) { return p.outdoor });
    var outMin = Math.min.apply(null, outVals);
    var outMax = Math.max.apply(null, outVals);
    var outAvg = outVals.reduce(function (a, b) { return a + b }, 0) / outVals.length;

    /* WW Min/Max */
    var wwVals = data.filter(function (p) { return p.dhw != null && p.dhw > 0 }).map(function (p) { return p.dhw });
    var wwMin = wwVals.length ? Math.min.apply(null, wwVals) : 0;
    var wwMax = wwVals.length ? Math.max.apply(null, wwVals) : 0;

    /* Brenner-Zyklen zählen */
    var cycles = 0, wasBurner = false;
    data.forEach(function (p) {
        if (p.burner && !wasBurner) cycles++;
        wasBurner = p.burner;
    });

    /* Heiz-Anteil */
    var heatPts = data.filter(function (p) { return p.mode === 'heating' }).length;
    var dhwPts = data.filter(function (p) { return p.mode === 'dhw' }).length;
    var totalPts = data.length;
    var heatPct = totalPts > 0 ? Math.round(heatPts / totalPts * 100) : 0;
    var dhwPct = totalPts > 0 ? Math.round(dhwPts / totalPts * 100) : 0;

    var parts = [];
    parts.push('Außen ' + F(outMin, 1) + '–' + F(outMax, 1) + '°C (⌀ ' + F(outAvg, 1) + '°C)');
    if (wwVals.length) parts.push('WW ' + F(wwMin, 1) + '–' + F(wwMax, 1) + '°C');
    parts.push(cycles + ' Brennerzyklen');
    if (heatPct > 0 || dhwPct > 0) parts.push('Heizung ' + heatPct + '% · WW ' + dhwPct + '% der Zeit');

    /* Bewertung */
    var note = '';
    if (wwMin > 0 && wwMin < 45) {
        note = ' · ⚠️ WW-Temperatur fiel unter 45°C (' + F(wwMin, 1) + '°C)';
    } else if (outMax - outMin > 15) {
        note = ' · ℹ️ Große Temperaturschwankung außen (' + F(outMax - outMin, 0) + '°C)';
    } else if (cycles === 0) {
        note = ' · ✅ Kein Brennerbetrieb im Zeitraum';
    }

    el.innerHTML = parts.join(' · ') + note;
}
