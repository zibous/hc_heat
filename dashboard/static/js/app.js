/* app.js – Theme, Helpers, Init */
'use strict';

var darkMode = localStorage.getItem('haco-theme') !== 'light';
function applyTheme() {
    document.body.classList.toggle('light', !darkMode);
    document.querySelector('.theme-btn').textContent = darkMode ? '🌙' : '☀️';
    localStorage.setItem('haco-theme', darkMode ? 'dark' : 'light');
    restoreBgColor();
}
function toggleTheme() { darkMode = !darkMode; applyTheme(); }
applyTheme();

/* Background Colorpicker */
function applyBgColor(color) {
    document.documentElement.style.setProperty('--bg', color);
    localStorage.setItem('haco-bg-color', color);
    document.getElementById('bgPicker').value = color;
    document.getElementById('bgResetBtn').style.display = '';
}
function resetBgColor() {
    document.documentElement.style.removeProperty('--bg');
    localStorage.removeItem('haco-bg-color');
    document.getElementById('bgResetBtn').style.display = 'none';
}
function restoreBgColor() {
    var saved = localStorage.getItem('haco-bg-color');
    if (saved) applyBgColor(saved);
    else { document.documentElement.style.removeProperty('--bg'); document.getElementById('bgResetBtn').style.display = 'none'; }
}
restoreBgColor();

/* Helpers */
var _ts = function () { return 't=' + Date.now(); };
var _fetch = function (url) { return fetch(url + (url.indexOf('?') > -1 ? '&' : '?') + _ts()); };
var F = function (v, d) { d = d || 0; return (v || 0).toLocaleString('de-DE', { minimumFractionDigits: d, maximumFractionDigits: d }); };
var fH = function (m) { if (!m) return '–'; return F(m / 60, 0) + ' h'; };
function det(k, v) { return '<div class="detail-item"><span class="detail-key">' + k + '</span><span class="detail-val">' + v + '</span></div>'; }
function detSection(t) { return '<div class="detail-section">' + t + '</div>'; }
function bL(v) { return v === true ? 'An' : v === false ? 'Aus' : '–'; }
function bC(v) { return v === true ? 'ok' : ''; }
function mL(m) { return { standby: '⏸ Standby', heating: '🔥 Heizbetrieb', dhw: '💧 Warmwasser', disinfection: '🧹 Desinfektion' }[m] || m; }
function mC(m) { return { standby: 'info', heating: 'heat', dhw: 'dhw', disinfection: 'warn' }[m] || 'info'; }

function toggleDGroup(id) {
    var el = document.getElementById('dg-' + id);
    if (!el) return;
    var sec = el.previousElementSibling;
    if (el.classList.toggle('hidden')) {
        sec.innerHTML = sec.innerHTML.replace(' ▾', ' ▸');
    } else {
        sec.innerHTML = sec.innerHTML.replace(' ▸', ' ▾');
    }
}

function modeSegments(active) {
    var modes = ['standby', 'heating', 'dhw', 'disinfection'];
    var labels = { standby: 'Standby', heating: 'Heizen', dhw: 'WW', disinfection: 'Desinf.' };
    return '<div class="mode-segments">' + modes.map(function (m) {
        return '<div class="mode-seg' + (m === active ? ' active' : '') + '" data-m="' + m + '" title="' + labels[m] + '"></div>';
    }).join('') + '</div>';
}

function onOffBar(isOn) {
    return '<div class="tile-onoff"><div class="seg ' + (isOn ? 'off' : 'on') + '" title="Aus"></div><div class="seg ' + (isOn ? 'on' : 'off') + '" title="An"></div></div>';
}

function stackedGauge(parts) {
    /* parts: [{val, color, label}] — gestapelter Balken */
    var total = parts.reduce(function (s, p) { return s + (p.val || 0); }, 0);
    if (total <= 0) return '';
    var h = '<div class="tile-gauge-stacked">';
    parts.forEach(function (p) {
        var pct = total > 0 ? (p.val / total * 100) : 0;
        if (pct > 0) h += '<div class="seg" style="width:' + pct + '%;background:' + p.color + '" title="' + (p.label || '') + ' ' + F(p.val, 1) + '"></div>';
    });
    return h + '</div>';
}

function tile(v, l, c, sub, icon, gauge, trend, bottom) {
    var h = '<div class="tile">';
    h += '<div class="tile-head"><span class="tile-head-lbl">' + l + '</span>';
    if (icon) h += '<span class="tile-head-icon">' + icon + '</span>';
    h += '</div>';
    h += '<div class="tile-val ' + (c || 'info') + '">' + v + '</div>';
    if (sub) h += '<div class="tile-sub">' + sub + '</div>';
    if (trend) h += '<div class="tile-trend">' + trend + '</div>';
    if (gauge) h += '<div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + Math.min(100, gauge.pct) + '%;background:' + (gauge.color || 'var(--accent)') + '"></div></div></div>';
    if (bottom) h += bottom;
    return h + '</div>';
}

function tileT(cur, l, c, prev, icon, gauge, sub) {
    var arrow = '', arrowCls = '';
    if (prev != null && cur != null) {
        var cv = parseFloat(String(cur).replace(/[^0-9,.\-]/g, '').replace(',', '.'));
        var pv = parseFloat(String(prev).replace(/[^0-9,.\-]/g, '').replace(',', '.'));
        if (!isNaN(cv) && !isNaN(pv)) {
            var d = cv - pv;
            if (d > 0.3) { arrow = '▲'; arrowCls = 'arrow-up'; }
            else if (d < -0.3) { arrow = '▼'; arrowCls = 'arrow-down'; }
            else { arrow = '●'; arrowCls = 'arrow-same'; }
        }
    }
    var h = '<div class="tile">';
    h += '<div class="tile-head"><span class="tile-head-lbl">' + l + '</span>';
    if (icon) h += '<span class="tile-head-icon">' + icon + '</span>';
    h += '</div>';
    h += '<div class="tile-val ' + (c || 'info') + '">' + cur + '</div>';
    if (sub) h += '<div class="tile-sub">' + sub + '</div>';
    if (prev != null) h += '<div class="tile-trend"><span class="' + arrowCls + '">' + arrow + '</span> ' + prev + '</div>';
    if (gauge) h += '<div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + Math.min(100, gauge.pct) + '%;background:' + (gauge.color || 'var(--accent)') + '"></div></div></div>';
    return h + '</div>';
}

/* Base-Path aus URL ableiten (nginx-fähig) */
var _bp = window.location.pathname.replace(/\/+$/, '') || '';

function cc() {
    return {
        text: darkMode ? '#e2e8f0' : '#0f172a',
        grid: darkMode ? '#1e2235' : '#e2e8f0',
        muted: darkMode ? '#64748b' : '#94a3b8'
    };
}

/* Init: Config laden, Daten laden, Auto-Refresh */
_fetch(_bp + '/api/config').then(function (r) { return r.json(); }).then(function (c) {
    if (c.title) document.getElementById('title').textContent = c.title;
    var sub = [];
    if (c.manufacturer && c.model) sub.push(c.manufacturer + ' ' + c.model);
    if (c.installed) sub.push('Installiert: ' + c.installed);
    document.getElementById('subtitle').textContent = sub.join(' · ');
    if (c.interval) document.getElementById('refreshInterval').textContent = c.interval;
    setInterval(loadData, (c.interval || 60) * 1000);
}).catch(function () { });

function loadData() {
    Promise.all([
        _fetch(_bp + '/api/live').then(function (r) { return r.json(); }),
        _fetch(_bp + '/api/history').then(function (r) { return r.json(); }),
        _fetch(_bp + '/api/config').then(function (r) { return r.json(); }).catch(function () { return {}; })
    ]).then(function (res) {
        var live = res[0];
        live.config_installed = res[2].installed || '';
        renderData(live);
        renderCharts(res[1].data || [], live.thermostat || {});
    }).catch(function () {
        document.getElementById('updateTime').textContent = 'Verbindung fehlgeschlagen';
    });
}
loadData();
