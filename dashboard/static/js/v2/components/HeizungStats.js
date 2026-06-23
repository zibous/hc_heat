// components/HeizungStats.js
// Kompakte Stat-Cards mit SVG-Icons und farbigen Detail-Rows

const F = (v, d = 2) => v != null ? Number(v).toFixed(d).replace('.', ',') : '--';
const ico = (path) => `<span class="stat-row-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg></span>`;
const icoInline = (path) => `<svg style="width:12px;height:12px;vertical-align:-1px;stroke:currentColor;stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round;display:inline" viewBox="0 0 24 24">${path}</svg>`;

function sparkline(values, color = '#f59e0b', w = 90, h = 26) {
  if (!values || values.length < 2) return '';
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const step = w / (values.length - 1);
  const pts = values.map((v, i) => `${(i * step).toFixed(1)},${(h - 2 - ((v - min) / range) * (h - 4)).toFixed(1)}`).join(' ');
  return `<svg width="${w}" height="${h}" style="display:block;flex-shrink:0;opacity:.8"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

// SVG Icon-Pfade (Lucide-Style)
const ICONS = {
  check: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  thermo: '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14 0-5.5 3.5-7.5 0 0 .5 4 2 5s2.17 2.97 2.17 4.73A5.5 5.5 0 0 1 12 16.5a5.5 5.5 0 0 1-3.5-2z"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
  drop: '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
  pump: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>',
  gas: '<path d="M4 10a7.31 7.31 0 0 0 10 10M5 12l5-5"/><path d="M12 22c3 0 7-3 7-7 0-3-2-5.5-4-7.5l-3 3"/>',
  coin: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  home: '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  bar: '<path d="M18 20V10M12 20V4M6 20v-6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2"/>',
};

function row(icon, label, value, color = '') {
  const style = color ? ` style="color:${color}"` : '';
  return `<div class="stat-row">${ico(ICONS[icon] || ICONS.check)}<span class="stat-row-lbl">${label}</span><span class="stat-row-val"${style}>${value}</span></div>`;
}

function card(title, hero, heroColor, badge, badgeColor, rows, extra = '', spark = '') {
  const badgeHtml = badge ? `<span class="stat-card-badge" style="background:${badgeColor}20;color:${badgeColor}">${badge}</span>` : '';
  const heroStyle = heroColor ? ` style="color:${heroColor}"` : '';
  return `<div class="stat-card">
    <div class="stat-card-hdr"><span class="stat-card-title">${title}</span>${badgeHtml}</div>
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div class="stat-card-hero"${heroStyle}>${hero}</div>
      ${spark}
    </div>
    <div class="stat-card-rows">${rows}</div>
    ${extra}
  </div>`;
}

export class HeizungStats {
  render() {
    return `<div class="section-title" style="margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Übersicht & Betriebsdaten</div>
    <div class="stats-grid" id="stats-grid">
      ${card('System & Betrieb', '—', '', '', '', '')}
      ${card('Anlagen-Komponenten', '—', '', '', '', '')}
      ${card('Heute Verbrauch', '—', '', '', '', '')}
      ${card('Energiebilanz', '—', '', '', '', '')}
    </div>`;
  }

  update(data, container) {
    if (!container || !data) return;
    const grid = container.querySelector('#stats-grid');
    if (!grid) return;

    const mode = data.mode || 'standby';
    const modeMap = { standby: 'Standby', heating: 'Heizen', dhw: 'Warmwasser', disinfecting: 'Desinfektion' };
    const displayMode = modeMap[mode] || mode;
    const isBurner = data.boiler?.burner_active || false;
    const errCount = data.errors?.count || 0;

    // Mode-Dauer
    let modeDur = '';
    if (data.mode_duration_sec) {
      const m = Math.round(data.mode_duration_sec / 60);
      modeDur = m > 60 ? `${Math.floor(m/60)}h ${m%60}m` : `${m} min`;
    }

    // Laufzeiten
    const rtTotal = Math.round((data.consumption?.burner_runtime_min || 0) / 60);
    const rtHeat = Math.round((data.consumption?.heating_runtime_min || 0) / 60);
    const rtDhw = Math.round((data.consumption?.dhw_runtime_min || 0) / 60);
    const starts = data.consumption?.burner_starts || 0;

    // Modus-Farbe als Dot vor dem Hero-Text
    const modeColors = { heating: 'var(--red, #ef4444)', dhw: 'var(--accent, #3b82f6)', disinfecting: 'var(--orange, #f59e0b)' };
    const modeColor = modeColors[mode] || 'var(--text-muted, #64748b)';
    const c1Hero = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${modeColor};margin-right:8px;vertical-align:middle"></span>${displayMode} · Brenner ${isBurner ? 'An' : 'Aus'}`;
    const c1Badge = errCount > 0 ? `${errCount} Fehler` : 'OK';
    const c1BadgeColor = errCount > 0 ? '#ef4444' : '#10b981';
    const c1Rows =
      row('clock', 'Modus seit', modeDur) +
      row('pump', 'Pumpe', `${data.boiler?.pump_modulation || 0}%`) +
      row('flame', 'Betriebszeit', `${rtTotal}h (${icoInline(ICONS.home)} ${rtHeat}h · ${icoInline(ICONS.drop)} ${rtDhw}h)`) +
      row('zap', 'Starts', starts.toLocaleString('de-DE')) +
      row('wrench', 'Service', `${data.boiler?.service_code || '0H'} · Wartung: ${data.boiler?.maintenance_date || '–'}`);

    // --- Card 2: Anlagen-Komponenten ---
    const boilerTemp = F(data.dhw?.curtemp, 1);
    const boilerSoll = data.thermostat?.wwk?.settemp || data.dhw?.settemp || 0;
    const boilerDeltaNum = data.dhw?.curtemp != null ? data.dhw.curtemp - boilerSoll : null;
    const deltaStr = boilerDeltaNum != null ? `(${boilerDeltaNum > 0 ? '+' : ''}${boilerDeltaNum.toFixed(1).replace('.', ',')}°C)` : '';
    const thermoMode = data.thermostat?.hc1?.mode || 'auto';
    const summerMode = data.thermostat?.hc1?.summermode || '–';
    const c2Hero = `<svg style="width:20px;height:20px;vertical-align:-3px;stroke:currentColor;stroke-width:2;fill:none;stroke-linecap:round;stroke-linejoin:round;display:inline" viewBox="0 0 24 24">${ICONS.drop}</svg> ${boilerTemp}°C ${deltaStr}`;
    const c2Rows =
      row('thermo', 'Thermostat', `${thermoMode} / ${data.thermostat?.hc1?.modetype || '–'}`) +
      row('sun', 'Betriebsart', summerMode) +
      row('home', 'Soll-Temp HZ', `${F(data.thermostat?.hc1?.seltemp, 1)}°C`) +
      row('drop', 'WW-Soll', `${F(data.thermostat?.wwk?.settemp, 0)}°C`) +
      row('gas', 'Gaszähler', `${F(data.gas?.display_m3, 3)} m³`);

    // --- Card 3: Heute Verbrauch ---
    const t = data.today || {};
    const c3Hero = `${F(t.cost_eur, 2)} €`;
    const c3Rows =
      row('zap', 'Energie', `${F(t.energy_kwh, 1)} kWh`, '#f59e0b') +
      row('home', 'Heizung', `${F(t.heat_kwh, 1)} kWh (${F(t.cost_heat_eur, 2)} €)`, '#ef4444') +
      row('drop', 'Warmwasser', `${F(t.dhw_kwh, 1)} kWh (${F(t.cost_dhw_eur, 2)} €)`, '#3b82f6') +
      row('gas', 'Gas', `${F(t.gas_m3, 3)} m³`) +
      row('clock', 'Brenner', `${t.burner_min || 0} min`);

    // --- Card 4: Energiebilanz (Heizung/Boiler Anteil) ---
    const hKwh = data.consumption?.energy_heat_kwh || 0;
    const wKwh = data.consumption?.energy_dhw_kwh || 0;
    const totKwh = data.consumption?.energy_total_kwh || 1;
    const hPct = Math.round((hKwh / totKwh) * 100);
    const wPct = 100 - hPct;
    const c4Hero = `${hPct}% / ${wPct}%`;
    const c4Rows =
      row('home', 'Heizung', `${Math.round(hKwh).toLocaleString('de-DE')} kWh`, '#ef4444') +
      row('drop', 'Warmwasser', `${Math.round(wKwh).toLocaleString('de-DE')} kWh`, '#3b82f6') +
      row('bar', 'Gesamt', `${Math.round(totKwh).toLocaleString('de-DE')} kWh`);
    const gauge4 = `<div class="stat-gauge"><div class="stat-gauge-seg" style="width:${hPct}%;background:#ef4444"></div><div class="stat-gauge-seg" style="width:${wPct}%;background:#3b82f6"></div></div>`;

    // --- Card 5: Geräte-Status ---
    // Installiert-seit berechnen
    let installedDays = '–';
    const installed = data.system?.installed || data._config?.installed;
    if (installed) {
      const instDate = new Date(installed);
      if (!isNaN(instDate)) {
        installedDays = Math.floor((Date.now() - instDate.getTime()) / 86400000).toLocaleString('de-DE');
      }
    }

    const boilerErr = data.errors?.boiler?.code;
    const thermoErr = data.errors?.thermostat?.code;
    const c5Rows =
      row('zap', 'EMS-ESP', 'Online', '#10b981') +
      row('flame', 'Vorlauf', `OK · ${F(data.boiler?.flow_temp, 1)}°C`, '#10b981') +
      row('thermo', 'Thermostat', `${boilerErr ? 'ERR ' + boilerErr : 'OK'} · ${thermoMode}/${data.thermostat?.hc1?.modetype || '–'}`, boilerErr ? '#ef4444' : '#10b981') +
      row('gas', 'Gaszähler', `${F(data.gas?.display_m3, 1)} m³`, '#10b981') +
      row('clock', 'Installiert seit', `${installedDays} Tage`);

    // Sparklines aus History-Daten (wenn verfügbar)
    const hist = data.history || [];
    const spark2 = hist.length > 5 ? sparkline(hist.slice(-24).map(p => p.dhw || 0), '#f59e0b') : '';
    const spark3 = hist.length > 5 ? sparkline(hist.slice(-24).map(p => p.flow || 0), '#10b981') : '';

    // --- Render ---
    grid.innerHTML =
      card('System & Betrieb', c1Hero, isBurner ? '#ef4444' : '', c1Badge, c1BadgeColor, c1Rows) +
      card('Anlagen-Komponenten', c2Hero, '#f59e0b', '', '', c2Rows, '', spark2) +
      card('Heute Verbrauch & Kosten', c3Hero, '#10b981', '', '', c3Rows, '', spark3) +
      card('Anteil Heizung / Boiler', c4Hero, '', '', '', c4Rows, gauge4) +
      card('Geräte-Status', 'Online', '#10b981', errCount > 0 ? 'Störung' : 'Alles OK', errCount > 0 ? '#ef4444' : '#10b981', c5Rows);
  }
}
