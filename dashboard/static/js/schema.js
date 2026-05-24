/* schema.js – Schematische Heizungsanlage als SVG */
'use strict';

function _renderFlow(b, dhw, gas, today, lc, th) {
    var burnerOn = b.burner_active === true;
    var heatOn = b.heating_active === true;
    var pumpOn = b.pump_active === true;
    var heatBurning = heatOn && burnerOn;  /* Aktiv heizend */
    var heatCoasting = heatOn && !burnerOn; /* Nachlauf */
    var dhwOn = dhw.charging === true || b.tapwater_active === true;
    var disOn = dhw.disinfecting === true;

    var cOff = '#3b4563', cHeat = '#ef4444', cDhw = '#3b82f6';
    var cGas = '#f59e0b', cCold = '#06b6d4', cGreen = '#10b981';
    var cVorlauf = heatBurning ? cHeat : (heatCoasting ? '#f59e0b' : cOff);
    var cRueck = heatBurning ? '#818cf8' : (heatCoasting ? '#a78bfa' : cOff);
    var cWWout = dhwOn || disOn ? cDhw : cOff;
    var cBurner = burnerOn ? cGas : cOff;
    var hc1 = th && th.hc1 ? th.hc1 : {};

    function lastParts(key) {
        var c = lc[key]; if (!c) return null;
        var t = new Date(c.start);
        var ts = t.getHours().toString().padStart(2, '0') + ':' + t.getMinutes().toString().padStart(2, '0');
        var dur = c.duration_min < 60 ? F(c.duration_min, 0) + 'm' : F(c.duration_min / 60, 1) + 'h';
        var line1 = 'Letzter: ' + ts + ' · ' + dur;
        var line2 = '';
        if (c.energy_kwh > 0) line2 += F(c.energy_kwh, 2) + ' kWh';
        if (c.gas_m3 > 0) line2 += (line2 ? ' · ' : '') + F(c.gas_m3, 3) + ' m³';
        return { line1: line1, line2: line2 };
    }

    var svg = '<svg viewBox="0 0 760 460" style="width:100%;max-height:460px">';
    svg += '<style>';
    svg += 'text{fill:#e2e8f0;font-family:system-ui,sans-serif}';
    svg += 'body.light text{fill:#0f172a}';
    svg += '.sl{font-size:11px;fill:#64748b}.sv{font-size:14px;font-weight:700}';
    svg += '.su{font-size:12px;fill:#64748b}.st{font-size:12px}';
    svg += '.pipe{stroke-width:3;fill:none;stroke-linecap:round}';
    svg += '.bx{rx:10;ry:10;stroke-width:2;fill:#1a1d27}';
    svg += 'body.light .bx{fill:#fff}';
    svg += '.pulse{animation:pp 2s infinite}';
    svg += '@keyframes pp{0%,100%{opacity:1}50%{opacity:.4}}';
    svg += '</style>';

    /* ── Gaszähler Box oben ── */
    svg += '<rect x="100" y="5" width="140" height="65" rx="10" ry="10" stroke-width="2" stroke="' + (burnerOn ? cGas : cOff) + '" style="fill:' + (burnerOn ? 'rgba(245,158,11,0.15)' : '#1e2235') + '"/>';
    svg += '<text x="170" y="26" text-anchor="middle" class="sv">⛽ Gaszähler</text>';
    svg += '<text x="170" y="43" text-anchor="middle" class="su">' + (gas ? F(gas.display_m3, 1) + ' m³' : '–') + ' · ' + (burnerOn ? '<tspan fill="' + cGas + '">Ein</tspan>' : 'Aus') + '</text>';
    if (today.gas_m3) svg += '<text x="170" y="58" text-anchor="middle" class="sl">Heute ' + F(today.gas_m3, 2) + ' m³</text>';
    if (burnerOn) svg += '<circle cx="115" cy="24" r="4" fill="' + cGas + '" class="pulse"/>';
    svg += '<line x1="170" y1="70" x2="170" y2="80" class="pipe" stroke="' + (burnerOn ? cGas : cOff) + '"/>';

    /* ── Kessel GB172-14 ── */
    svg += '<rect x="80" y="75" width="180" height="140" rx="10" ry="10" stroke-width="2" stroke="' + (burnerOn ? cGas : cOff) + '" style="fill:' + (burnerOn ? 'rgba(245,158,11,0.15)' : '#1e2235') + '"/>';
    svg += '<text x="170" y="97" text-anchor="middle" class="sv">GB172-14</text>';
    svg += '<text x="170" y="114" text-anchor="middle" class="st" fill="' + cBurner + '">' + (burnerOn ? '🔥 ' + F(b.current_power_kw, 1) + ' kW' : '🔥 Aus') + '</text>';
    svg += '<text x="170" y="130" text-anchor="middle" class="su">Vorlauf ' + F(b.flow_temp, 1) + '°C · Soll ' + F(b.flow_set_temp, 0) + '°C</text>';
    svg += '<text x="170" y="146" text-anchor="middle" class="su">Pumpe ' + (pumpOn ? 'An ' + F(b.pump_modulation) + '%' : 'Aus') + '</text>';
    var flowPct = (b.flow_set_temp || 28) > 0 ? Math.min(100, (b.flow_temp || 0) / (b.flow_set_temp || 28) * 100) : 0;
    svg += '<rect x="95" y="155" width="150" height="4" rx="2" fill="' + cOff + '"/>';
    svg += '<rect x="95" y="155" width="' + (flowPct * 1.5) + '" height="4" rx="2" fill="' + cHeat + '"/>';
    var pumpPct = b.pump_modulation || 0;
    svg += '<rect x="95" y="163" width="150" height="4" rx="2" fill="' + cOff + '"/>';
    svg += '<rect x="95" y="163" width="' + (pumpPct * 1.5) + '" height="4" rx="2" fill="' + cGreen + '"/>';
    if (burnerOn) svg += '<circle cx="100" cy="100" r="4" fill="' + cGas + '" class="pulse"/>';

    /* ── Speicher BS 150 ── */
    svg += '<rect x="80" y="220" width="180" height="105" rx="10" ry="10" stroke-width="2" stroke="' + (dhwOn || disOn ? cDhw : cOff) + '" style="fill:' + (dhwOn || disOn ? 'rgba(59,130,246,0.15)' : '#1e2235') + '"/>';
    svg += '<text x="170" y="242" text-anchor="middle" class="sv">BS 150</text>';
    svg += '<text x="170" y="259" text-anchor="middle" class="st" fill="' + cDhw + '">💧 ' + F(dhw.curtemp, 1) + '°C · Soll ' + F(dhw.settemp, 0) + '°C</text>';
    var wwStatus = disOn ? '🧹 Desinfektion' : dhwOn ? '● Laden' : 'Bereit';
    var wwColor = disOn ? cGas : dhwOn ? cDhw : cOff;
    svg += '<text x="170" y="276" text-anchor="middle" class="su" fill="' + wwColor + '">' + wwStatus + '</text>';
    /* WW Temperatur Gauge: Ist vs Soll */
    var wwPct = (dhw.settemp || 57) > 0 ? Math.min(100, (dhw.curtemp || 0) / (dhw.settemp || 57) * 100) : 0;
    svg += '<rect x="95" y="285" width="150" height="4" rx="2" fill="' + cOff + '"/>';
    svg += '<rect x="95" y="285" width="' + (wwPct * 1.5) + '" height="4" rx="2" fill="' + cDhw + '"/>';
    if (dhwOn || disOn) svg += '<circle cx="100" cy="245" r="4" fill="' + wwColor + '" class="pulse"/>';
    svg += '<line x1="170" y1="205" x2="170" y2="220" class="pipe" stroke="' + cOff + '"/>';

    /* ── Vorlauf → Heizkörper ── */
    svg += '<line x1="260" y1="110" x2="470" y2="110" class="pipe" stroke="' + cVorlauf + '"/>';
    svg += '<polygon points="465,105 475,110 465,115" fill="' + cVorlauf + '"/>';
    svg += '<text x="390" y="102" class="sl" fill="' + cVorlauf + '">Vorlauf</text>';
    /* Rücklauf ← */
    svg += '<line x1="260" y1="160" x2="470" y2="160" class="pipe" stroke="' + cRueck + '"/>';
    svg += '<polygon points="265,155 255,160 265,165" fill="' + cRueck + '"/>';
    svg += '<text x="390" y="176" class="sl" fill="' + cRueck + '">Rücklauf</text>';
    if (heatBurning) svg += '<circle cx="480" cy="95" r="4" fill="' + cHeat + '" class="pulse"/>';

    /* ── Heizkörper-Block ── */
    var hkColor = heatBurning ? cHeat : (heatCoasting ? '#f59e0b' : cOff);
    var hkFill = heatBurning ? 'rgba(239,68,68,0.15)' : (heatCoasting ? 'rgba(245,158,11,0.1)' : '#1e2235');
    var hkStatus = heatBurning ? '● Aktiv' : (heatCoasting ? '○ Nachlauf' : 'Aus');
    svg += '<rect x="480" y="75" width="250" height="150" rx="10" ry="10" stroke-width="2" stroke="' + hkColor + '" style="fill:' + hkFill + '"/>';
    svg += '<text x="605" y="100" text-anchor="middle" class="sv">🏠 Heizkörper</text>';
    svg += '<text x="605" y="118" text-anchor="middle" class="st" fill="' + hkColor + '">' + hkStatus + '</text>';
    svg += '<text x="605" y="134" text-anchor="middle" class="su">Vorlauf ' + F(b.flow_temp, 1) + '°C</text>';
    /* Heizkörper Vorlauf Gauge */
    svg += '<rect x="510" y="142" width="190" height="4" rx="2" fill="' + cOff + '"/>';
    svg += '<rect x="510" y="142" width="' + (flowPct * 1.9) + '" height="4" rx="2" fill="' + cHeat + '"/>';
    var lpH = lastParts('heating');
    if (lpH) {
        svg += '<text x="605" y="162" text-anchor="middle" class="sl">' + lpH.line1 + '</text>';
        if (lpH.line2) svg += '<text x="605" y="178" text-anchor="middle" class="sl">' + lpH.line2 + '</text>';
    }

    /* ── WW Abnahme rechts ── */
    svg += '<line x1="260" y1="270" x2="470" y2="270" class="pipe" stroke="' + cWWout + '"/>';
    svg += '<polygon points="465,265 475,270 465,275" fill="' + cWWout + '"/>';
    svg += '<rect x="480" y="245" width="250" height="150" rx="10" ry="10" stroke-width="2" stroke="' + (dhwOn || disOn ? cDhw : cOff) + '" style="fill:' + (dhwOn || disOn ? 'rgba(59,130,246,0.15)' : '#1e2235') + '"/>';
    svg += '<text x="605" y="270" text-anchor="middle" class="sv">🚿 Warmwasser</text>';
    svg += '<text x="605" y="288" text-anchor="middle" class="su">' + F(dhw.curtemp, 1) + '°C</text>';
    /* WW Gauge */
    svg += '<rect x="510" y="297" width="190" height="4" rx="2" fill="' + cOff + '"/>';
    svg += '<rect x="510" y="297" width="' + (wwPct * 1.9) + '" height="4" rx="2" fill="' + cDhw + '"/>';
    var lpD = lastParts('dhw');
    if (lpD) {
        svg += '<text x="605" y="317" text-anchor="middle" class="sl">' + lpD.line1 + '</text>';
        if (lpD.line2) svg += '<text x="605" y="333" text-anchor="middle" class="sl">' + lpD.line2 + '</text>';
    }

    /* ── Kaltwasser ── */
    svg += '<line x1="170" y1="325" x2="170" y2="400" class="pipe" stroke="' + cCold + '"/>';
    svg += '<text x="185" y="390" class="sl" fill="' + cCold + '">Kaltwasser</text>';

    /* ── RC310 Thermostat ── */
    svg += '<rect x="5" y="145" width="65" height="55" rx="10" ry="10" stroke-width="2" stroke="' + cOff + '" style="fill:#1e2235"/>';
    svg += '<text x="37" y="168" text-anchor="middle" class="sv" style="font-size:12px">RC310</text>';
    svg += '<text x="37" y="184" text-anchor="middle" class="sl">' + (hc1.mode || '–') + '</text>';
    svg += '<line x1="70" y1="172" x2="80" y2="172" class="pipe" stroke="' + cOff + '"/>';

    svg += '</svg>';

    /* Desktop: SVG Schema, Mobile: Kacheln (Schwelle 900px) */
    var isMobile = window.innerWidth < 900;
    document.getElementById('flowChart').style.display = isMobile ? 'none' : '';
    document.getElementById('flowMobile').style.display = isMobile ? '' : 'none';

    /* Immer beide rendern für Orientierungswechsel */
    document.getElementById('flowChart').innerHTML = svg;

    var fc = '<div class="tiles">';
    fc += '<div class="tile' + (burnerOn ? ' bg-gas' : '') + '">' + '<div class="tile-head"><span class="tile-head-lbl">Gas</span><span class="tile-head-icon">⛽</span></div><div class="tile-val ' + (burnerOn ? 'gas' : '') + '">' + (gas ? F(gas.display_m3, 1) + ' m³' : '–') + '</div><div class="tile-sub">Heute ' + F(today.gas_m3, 2) + ' m³' + (burnerOn ? ' · <b>Ein</b>' : '') + '</div></div>';
    fc += '<div class="tile' + (burnerOn ? ' bg-heat' : '') + '">' + '<div class="tile-head"><span class="tile-head-lbl">GB172-14</span><span class="tile-head-icon">🔥</span></div><div class="tile-val ' + (burnerOn ? 'heat' : '') + '">' + F(b.flow_temp, 1) + '°C</div><div class="tile-sub">' + (burnerOn ? '🔥 ' + F(b.current_power_kw, 1) + ' kW' : '🔥 Aus · Soll ' + F(b.flow_set_temp, 0) + '°C') + '</div><div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + flowPct + '%;background:' + cHeat + '"></div></div></div></div>';
    fc += '<div class="tile' + (heatOn ? ' bg-heat' : '') + '">' + '<div class="tile-head"><span class="tile-head-lbl">Heizkörper</span><span class="tile-head-icon">🏠</span></div><div class="tile-val ' + (heatOn ? 'heat' : '') + '">' + (heatOn ? '● Aktiv' : 'Aus') + '</div><div class="tile-sub">Vorlauf ' + F(b.flow_temp, 1) + '°C</div><div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + flowPct + '%;background:' + cHeat + '"></div></div></div></div>';
    fc += '<div class="tile' + (dhwOn || disOn ? ' bg-dhw' : '') + '">' + '<div class="tile-head"><span class="tile-head-lbl">BS 150 WW</span><span class="tile-head-icon">💧</span></div><div class="tile-val ' + (dhwOn ? 'dhw' : '') + '">' + F(dhw.curtemp, 1) + '°C</div><div class="tile-sub">' + wwStatus + ' · Soll ' + F(dhw.settemp, 0) + '°C</div><div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + wwPct + '%;background:' + cDhw + '"></div></div></div></div>';
    fc += '<div class="tile"><div class="tile-head"><span class="tile-head-lbl">RC310</span><span class="tile-head-icon">🌡️</span></div><div class="tile-val">' + (hc1.mode || '–') + '</div><div class="tile-sub">' + (hc1.modetype || '') + '</div></div>';
    fc += '</div>';
    document.getElementById('flowMobile').innerHTML = fc;
}
