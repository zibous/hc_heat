/* daily.js – Energie/Kosten/Laufzeiten Chart + CSV Export */
'use strict';

var dailyChart = null;
var _dailyRefresh = null;

function exportCSV() {
    window.location.href = _bp + '/api/export?days=30';
}

function loadDaily(from, to) {
    var url = _bp + '/api/daily?from=' + from + '&to=' + to;
    _fetch(url).then(function (r) { return r.json(); }).then(function (res) { renderDaily(res.data || []); }).catch(function () { });
}

function renderDaily(data) {
    if (!data || !data.length) return;
    var c = cc();
    _fetch(_bp + '/api/config').then(function (r) { return r.json(); }).then(function (cfg) {
        _renderDailyInner(data, c, cfg.gas_price_kwh || 0.103);
    }).catch(function () { _renderDailyInner(data, c, 0.103); });
}

function _renderDailyInner(data, c, gpk) {
    try {
        var labels = data.map(function (d) {
            if (d.day.indexOf(':') > -1) return d.day;
            var parts = d.day.split('-');
            if (parts.length === 2) return parts[1] + '/' + parts[0];
            return parts[2] + '.' + parts[1];
        });

        var disData = data.map(function (d) {
            if (d.day.indexOf(':') > -1) return 0;
            var dt = new Date(d.day);
            return (!isNaN(dt) && dt.getDay() === 6) ? Math.min(d.dhw_kwh, d.energy_kwh * 0.05) : 0;
        });
        var wwOnly = data.map(function (d, i) { return Math.max(0, d.dhw_kwh - disData[i]); });

        var ctx = document.getElementById('dailyChart').getContext('2d');
        if (dailyChart) dailyChart.destroy();
        dailyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: '🏠 Heizung', data: data.map(function (d) { return d.heat_kwh; }), backgroundColor: 'rgba(239,68,68,0.7)', stack: 'kwh', yAxisID: 'y' },
                    { label: '💧 Warmwasser', data: wwOnly, backgroundColor: 'rgba(59,130,246,0.7)', stack: 'kwh', yAxisID: 'y' },
                    { label: '🧹 Desinfektion', data: disData, backgroundColor: 'rgba(245,158,11,0.7)', stack: 'kwh', yAxisID: 'y' },
                    { label: '⛽ Gas m³', data: data.map(function (d) { return d.gas_m3 || 0; }), type: 'line', borderColor: '#f59e0b', borderWidth: 2, pointRadius: 2, tension: .3, yAxisID: 'y1', fill: false, borderDash: [4, 2] },
                    { label: '💰 Kosten €', data: data.map(function (d) { return Math.round(d.energy_kwh * gpk * 100) / 100; }), type: 'line', borderColor: '#10b981', borderWidth: 2, pointRadius: 3, tension: .3, yAxisID: 'y1', fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: c.text, font: { size: 11 }, usePointStyle: true } } },
                scales: {
                    x: { ticks: { color: c.muted, font: { size: 10 } }, grid: { color: c.grid }, stacked: true },
                    y: { title: { display: true, text: 'kWh', color: c.muted }, ticks: { color: c.muted }, grid: { color: c.grid }, stacked: true, position: 'left' },
                    y1: { title: { display: true, text: 'm³ / €', color: c.muted }, ticks: { color: c.muted }, grid: { display: false }, position: 'right' }
                }
            }
        });

        /* Zusammenfassung */
        var sumE = 0, sumH = 0, sumD = 0, sumG = 0, sumB = 0, sumDis = 0;
        data.forEach(function (d, i) { sumE += d.energy_kwh; sumH += d.heat_kwh; sumD += d.dhw_kwh; sumG += d.gas_m3; sumB += d.burner_min; sumDis += disData[i]; });
        var sumWW = sumD - sumDis, days = data.length;
        var s = '<div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center;padding:6px 0">';
        s += '<span>Σ <b>' + F(sumE, 1) + '</b> kWh</span>';
        s += '<span style="color:var(--heat)">🏠 ' + F(sumH, 1) + ' kWh</span>';
        s += '<span style="color:var(--dhw)">💧 ' + F(sumWW, 1) + ' kWh</span>';
        if (sumDis > 0) s += '<span style="color:var(--orange)">🧹 ' + F(sumDis, 1) + ' kWh</span>';
        s += '<span>⛽ ' + F(sumG, 2) + ' m³</span>';
        s += '<span style="color:var(--green)">💰 ' + F(sumE * gpk, 2) + ' €</span>';
        s += '<span>⏱ ' + fH(sumB) + '</span>';
        if (days > 1) s += '<span style="color:var(--muted)">⌀ ' + F(sumE / days, 1) + ' kWh/' + (days > 90 ? 'Monat' : 'Tag') + '</span>';
        s += '</div>';
        document.getElementById('mainTable').innerHTML = s;
    } catch (e) {
        document.getElementById('mainTable').textContent = 'Fehler: ' + e.message;
    }
}

/* DateSelector initialisieren */
_dailyRefresh = initDateSelector(document.getElementById('dailyPeriodSelector'), function (sel) {
    var p = sel.params;
    if (sel.period === 'today') {
        loadDaily(null, null, 1);
    } else {
        loadDaily(p.from, p.to);
    }
});
