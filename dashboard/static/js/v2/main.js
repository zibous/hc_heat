// main.js – Entry-Point für das Heizungs-Dashboard v2
import { HeizungDashboard } from './HeizungDashboard.js';

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
  themeBtn.addEventListener('click', () => {
    const body = document.body;
    const isLight = body.classList.toggle('light');
    themeBtn.textContent = isLight ? '☀️' : '🌙';
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
  });
  // Restore
  if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light');
    themeBtn.textContent = '☀️';
  }
}
