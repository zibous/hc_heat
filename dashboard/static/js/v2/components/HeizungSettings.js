// components/HeizungSettings.js
// Erweiterte System-Einstellungen als kompakte Stat-Cards

const F = (v, d = 2) => v != null ? Number(v).toFixed(d).replace('.', ',') : '--';
const ico = (path) => `<span class="stat-row-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg></span>`;

const ICONS = {
  thermo: '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14 0-5.5 3.5-7.5 0 0 .5 4 2 5s2.17 2.97 2.17 4.73A5.5 5.5 0 0 1 12 16.5a5.5 5.5 0 0 1-3.5-2z"/>',
  drop: '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
  gas: '<path d="M4 10a7.31 7.31 0 0 0 10 10M5 12l5-5"/><path d="M12 22c3 0 7-3 7-7 0-3-2-5.5-4-7.5l-3 3"/>',
  home: '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
  bar: '<path d="M18 20V10M12 20V4M6 20v-6"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
};

function row(icon, label, value, color = '') {
  const style = color ? ` style="color:${color}"` : '';
  return `<div class="stat-row">${ico(ICONS[icon] || ICONS.wrench)}<span class="stat-row-lbl">${label}</span><span class="stat-row-val"${style}>${value}</span></div>`;
}

function card(title, rows) {
  return `<div class="stat-card">
    <div class="stat-card-hdr"><span class="stat-card-title">${title}</span></div>
    <div class="stat-card-rows">${rows}</div>
  </div>`;
}

export class HeizungSettings {
  render() {
    return `
      <div class="section-title" style="margin: 2rem 0 1rem 0; font-size: 1.1rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Erweiterte System-Werte</div>
      <div class="stats-grid" id="settings-grid"></div>
    `;
  }

  update(data, container) {
    if (!container || !data) return;
    const grid = container.querySelector('#settings-grid');
    if (!grid) return;

    const b = data.boiler || {};
    const dhw = data.dhw || {};
    const g = data.gas || {};
    const c = data.consumption || {};
    const t = data.thermostat || {};
    const hc = t.hc1 || {};
    const wwk = t.wwk || {};

    // Card 1: Kessel & Warmwasser
    const c1 = row('wrench', 'Service-Code', b.service_code || '–') +
      row('clock', 'Wartung', b.maintenance_date || '–') +
      row('flame', 'Nennleistung', `${b.nominal_power_kw || 14} kW`) +
      row('zap', 'Akt. Leistung', `${F(b.current_power_kw, 1)} kW`) +
      row('wrench', 'Pumpe Modus', b.pump_mode || '–') +
      row('shield', 'Frostschutz', `${hc.nofrostmode || 'Aus'} ${F(hc.nofrosttemp, 0)}°C`) +
      row('drop', 'WW Komfort', dhw.comfort || '–') +
      row('drop', 'Speichertyp', dhw.storage_type || '–') +
      row('thermo', 'Vorlauf-Offset', `${F(dhw.flowtempoffset, 0)}°C`);

    // Card 2: Gaszähler & Energie
    const c2 = row('gas', 'Zählerstand', `${F(g.display_m3, 3)} m³`) +
      row('gas', 'Seit ESP-Install', `${F(g.total_m3, 3)} m³`) +
      row('clock', 'Zeitstempel', g.timestamp || '–') +
      row('bar', 'Energie Gesamt', `${F(c.energy_total_kwh, 2)} kWh`) +
      row('home', 'Heizung', `${F(c.energy_heat_kwh, 2)} kWh`, '#ef4444') +
      row('drop', 'Warmwasser', `${F(c.energy_dhw_kwh, 2)} kWh`, '#3b82f6');

    // Card 3: Heizkreis 1
    const c3 = row('home', 'Betriebsart', `${hc.mode || '–'} / ${hc.modetype || '–'}`) +
      row('thermo', 'Raumtemp Soll', `${F(hc.seltemp, 1)}°C`) +
      row('thermo', 'Vorlauf berechnet', `${F(hc.targetflowtemp, 0)}°C`) +
      row('thermo', 'Vorlauf Min/Max', `${F(hc.minflowtemp, 0)} / ${F(hc.maxflowtemp, 0)}°C`) +
      row('home', 'Heizungstyp', hc.heatingtype || '–') +
      row('sun', 'Sommerbetrieb', hc.summermode || '–') +
      row('wrench', 'Steuermodus', hc.controlmode || '–') +
      row('clock', 'Programm', hc.program || '–');

    // Card 4: WWK Thermostat
    const c4 = row('drop', 'Betriebsart', wwk.mode || '–') +
      row('thermo', 'Solltemp', `${F(wwk.settemp, 0)}°C`) +
      row('thermo', 'Solltemp niedrig', `${F(wwk.settemplow, 0)}°C`) +
      row('clock', 'Zirkulation', wwk.circmode || '–') +
      row('shield', 'Desinfektion', `${wwk.disinfectday || '–'} · ${wwk.disinfecttime || 0} min`) +
      row('clock', 'Ladedauer', `${wwk.chargeduration || 0} min`);

    grid.innerHTML = card('Kessel & Warmwasser', c1) +
      card('Gaszähler & Energie', c2) +
      card('Heizkreis 1 (RC310)', c3) +
      card('WWK Thermostat', c4);
  }
}
