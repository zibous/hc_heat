// main.js – Entry-Point für das Heizungs-Dashboard v2
import { HeizungDashboard } from './HeizungDashboard.js';
import { getAppleIcon } from './components/icons.js';

const dashboard = new HeizungDashboard('dashboard-container');

const REFRESH_INTERVAL_SEC = 60;
let countdown = REFRESH_INTERVAL_SEC;
let historyLoaded = false;

/**
 * Holt Live-Daten + History/Daily und aktualisiert das Dashboard.
 * Nur 1 API-Call pro Refresh (live), History+Daily nur beim Start.
 */
async function fetchData() {
  try {
    const res = await fetch('./api/live');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // History + Daily nur beim ersten Laden (oder alle 5 Min)
    if (!historyLoaded) {
      const [hRes, dRes] = await Promise.all([
        fetch('./api/history').catch(() => null),
        fetch('./api/daily?days=' + (localStorage.getItem('heat-daily-period') || '14')).catch(() => null)
      ]);

      if (hRes && hRes.ok) {
        const h = await hRes.json();
        if (h && h.data) data.history = h.data;
      }
      if (dRes && dRes.ok) {
        const d = await dRes.json();
        if (d && d.data) data.daily_history = d.data;
      }
      historyLoaded = true;
    }

    // Config-Daten für Installiert-seit injizieren
    if (_configData.installed) data._config = _configData;

    dashboard.update(data);

    // Header-Update-Timestamp
    if (data.timestamp) {
      const el = document.getElementById('header-update');
      if (el) {
        const d = new Date(data.timestamp);
        el.textContent = `Update: ${d.toLocaleDateString('de-DE')} ${d.toLocaleTimeString('de-DE', {hour:'2-digit',minute:'2-digit'})}`;
      }
    }

    countdown = REFRESH_INTERVAL_SEC;
    updateTimerUI();
  } catch (err) {
    console.error('Datenabruf fehlgeschlagen:', err);
    countdown = 10;
  }
}

function updateTimerUI() {
  const el = document.getElementById('refreshInterval');
  if (el) el.textContent = countdown;
}

// --- Start ---
fetchData();

// Config laden (Titel, Modell, Installationsdatum)
let _configData = {};
fetch('./api/config').then(r => r.json()).then(cfg => {
  _configData = cfg;
  if (cfg.title) document.getElementById('title').textContent = cfg.title;
  const sub = [];
  if (cfg.manufacturer) sub.push(cfg.manufacturer);
  if (cfg.model) sub.push(cfg.model);
  if (cfg.installed) sub.push('Installiert: ' + cfg.installed.substring(0, 10));
  if (sub.length) document.getElementById('subtitle').textContent = sub.join(' · ');
}).catch(() => {});

setInterval(() => {
  countdown--;
  if (countdown <= 0) {
    fetchData();
  } else {
    updateTimerUI();
  }
}, 1000);

// History alle 5 Minuten neu laden
setInterval(() => { historyLoaded = false; }, 300000);


// Theme Toggle
const themeBtn = document.getElementById('themeBtn');
if (themeBtn) {
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.classList.toggle('light', theme === 'light');
    themeBtn.innerHTML = theme === 'dark' ? getAppleIcon('sun', 16, '#f59e0b') : getAppleIcon('moon', 16, '#64748b');
    // Chart.js Gridlines und Texte aktualisieren
    syncChartColors();
  }

  const savedTheme = localStorage.getItem('theme') || 'dark';
  applyTheme(savedTheme);

  themeBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
  });
}

function syncChartColors() {
  const style = getComputedStyle(document.documentElement);
  const text = style.getPropertyValue('--text').trim() || '#e2e8f0';
  const muted = style.getPropertyValue('--text-muted').trim() || '#8892a4';
  const grid = style.getPropertyValue('--border').trim() || '#2e3350';

  // Alle registrierten Chart.js Instanzen updaten
  const charts = Object.values(Chart.instances || {});
  for (const chart of charts) {
    if (!chart || !chart.options) continue;
    const scales = chart.options.scales || {};
    for (const key of Object.keys(scales)) {
      if (scales[key].ticks) scales[key].ticks.color = muted;
      if (scales[key].grid) scales[key].grid.color = grid;
      if (scales[key].title) scales[key].title.color = muted;
    }
    if (chart.options.plugins?.legend?.labels) {
      chart.options.plugins.legend.labels.color = text;
    }
    chart.update('none');
  }
}
/* ----------------------------------------------------
   INFO
---------------------------------------------------- */
const appinfo = {
  name: "✓ heizungsanlage-dashboard ",
  app: "hc_smet",
  version: "3.0.0"
};

console.info(
  "%c " + appinfo.name + "    %c ▪︎▪︎▪︎▪︎ Version: " + appinfo.version + " ▪︎▪︎▪︎▪︎ ",
  "color:#FFFFFF; background:#3498db;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0",
  "color:#2c3e50; background:#ecf0f1;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0"
);
