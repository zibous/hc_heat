/* render.js – renderData: Status, Flowchart, Temperaturen, Details */
'use strict';

function renderData(d) {
    try {
        if (!d || !d.timestamp) { document.getElementById('statusRow').innerHTML = tile('–', 'Warte auf Daten'); return; }
        var b = d.boiler || {}, s = d.system || {}, dhw = d.dhw || {}, hc = d.heating_circuit || {};
        var con = d.consumption || {}, costs = d.costs || {}, gas = d.gas, err = d.errors || {};
        var mode = d.mode || 'standby', pv = d.prev || {}, th = d.thermostat || {};
        var today = d.today || {};

        document.getElementById('updateTime').textContent = 'Update: ' + new Date(d.timestamp).toLocaleString('de-DE');

        /* Modus-Dauer */
        var modeSec = d.mode_duration_sec || 0;
        var modeDur = modeSec >= 3600 ? Math.floor(modeSec / 3600) + 'h ' + Math.floor((modeSec % 3600) / 60) + 'min' : Math.floor(modeSec / 60) + ' min';
        var modeSince = d.mode_since ? new Date(d.mode_since).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : '';

        /* Status-Kacheln mit Trend */
        var sr = '';
        var prevMode = (pv.mode && pv.mode !== mode) ? 'vorher: ' + mL(pv.mode) : null;
        sr += tile(mL(mode), 'Betriebsmodus', mC(mode), modeSince ? 'seit ' + modeSince + ' · ' + modeDur : '', '⚙️', null, prevMode, modeSegments(mode));
        var bPct = b.burner_power_percent || 0;
        var bPrev = pv.burner_power != null && pv.burner_power !== bPct ? 'vorher ' + F(pv.burner_power) + '%' : null;
        sr += tile(bL(b.burner_active), 'Brenner', bC(b.burner_active), b.burner_active ? F(bPct) + '% · ' + F(b.current_power_kw, 1) + ' kW' : null, '🔥', null, bPrev, onOffBar(b.burner_active));
        var pMod = b.pump_modulation || 0;
        var pPrev = pv.pump_modulation != null && pv.pump_modulation !== pMod ? 'vorher ' + F(pv.pump_modulation) + '%' : null;
        sr += tile(bL(b.pump_active), 'Pumpe', bC(b.pump_active), b.pump_active ? F(pMod) + '%' : null, '💨', { pct: pMod, color: 'var(--green)' }, pPrev);
        /* Energie: gestapelte Gauge Heizung (rot) + WW (blau) */
        var hKwh = today.heat_kwh || 0, dKwh = today.dhw_kwh || 0;
        var eTotal = today.energy_kwh || 1;
        var gTotal = today.gas_m3 || 0;
        var gHeat = eTotal > 0 ? Math.round(gTotal * (hKwh / eTotal) * 1000) / 1000 : 0;
        var gWW = Math.max(0, Math.round((gTotal - gHeat) * 1000) / 1000);
        sr += tile(F(today.energy_kwh, 1) + '<span class="tile-unit">kWh</span>', 'Heute Energie', 'gas', 'Heizung ' + F(hKwh, 1) + ' · Boiler ' + F(dKwh, 1), '⚡', null, null, stackedGauge([{ val: hKwh, color: 'var(--heat)', label: 'Heizung' }, { val: dKwh, color: 'var(--dhw)', label: 'WW' }]));
        var gasLabel = 'Heute Gas';
        var gasSub = 'Heizung ' + F(gHeat, 2) + ' · Boiler ' + F(gWW, 2);
        if (b.burner_active) gasSub = '● Gasbezug aktiv · ' + gasSub;
        sr += tile(F(today.gas_m3, 2) + '<span class="tile-unit">m³</span>', gasLabel, b.burner_active ? 'warn' : 'gas', gasSub, '⛽', null, null, stackedGauge([{ val: gHeat, color: 'var(--heat)', label: 'Heizung' }, { val: gWW, color: 'var(--dhw)', label: 'WW' }]));
        /* Kosten: gestapelte Gauge Heizung + WW */
        var hEur = today.cost_heat_eur || 0, dEur = today.cost_dhw_eur || 0;
        sr += tile(F(today.cost_eur || 0, 2) + '<span class="tile-unit">€</span>', 'Heute Kosten', 'gas', 'Heizung ' + F(hEur, 2) + ' · Boiler ' + F(dEur, 2), '💰', null, null, stackedGauge([{ val: hEur, color: 'var(--heat)', label: 'Heizung' }, { val: dEur, color: 'var(--dhw)', label: 'WW' }]));
        document.getElementById('statusRow').innerHTML = '<div class="tiles" style="width:100%;margin:0">' + sr + '</div>';

        /* Info-Kacheln: Fehler, Heizbetrieb, Betriebszeiten, Status */
        _renderInfoRow(d, b, err, th, con, gas);

        /* Flowchart */
        _renderFlow(b, dhw, gas, today, d.last_cycles || {}, d.thermostat || {});

        /* Status-Banner: Fehler oder OK */
        _renderStatusBanner(err);

        /* 24h Progress-Bar */
        _renderProgressBar(d);

        /* Temperaturen */
        _renderTemps(b, dhw, s, pv, today, d.thermostat || {});

        /* Erweiterte Werte */
        _renderDetails(b, s, dhw, gas, con, err, th);
    } catch (e) { console.error('renderData error:', e); }
}

/* _renderFlow ist in schema.js */

function _renderTemps(b, dhw, s, pv, today, th) {
    var tt = '';
    var hc1 = th && th.hc1 ? th.hc1 : {};
    function gPct(v, lo, hi) { return Math.max(0, Math.min(100, ((v || 0) - lo) / (hi - lo) * 100)); }

    /* Vorlauf: Gauge zeigt Ist relativ zum Soll (0°C = 0%, Soll = 100%) */
    var flowSoll = b.flow_set_temp || 28;
    tt += tileT(F(b.flow_temp, 1) + '<span class="tile-unit">°C</span>', 'Vorlauf', 'heat',
        pv.flow_temp != null ? F(pv.flow_temp, 1) + '°C' : null, '🌡️',
        { pct: flowSoll > 0 ? gPct(b.flow_temp, 0, flowSoll) : 0, color: 'var(--heat)' },
        'Soll ' + F(b.flow_set_temp, 1) + '°C');

    /* WW: Gauge zeigt Ist relativ zum Soll */
    var wwSoll = dhw.settemp || 57;
    tt += tileT(F(dhw.curtemp, 1) + '<span class="tile-unit">°C</span>', 'Warmwasser', 'dhw',
        pv.dhw_temp != null ? F(pv.dhw_temp, 1) + '°C' : null, '💧',
        { pct: wwSoll > 0 ? gPct(dhw.curtemp, 0, wwSoll) : 0, color: 'var(--dhw)' },
        'Soll ' + F(dhw.settemp, 1) + '°C');

    tt += tile(F(dhw.disinfection_temp || 0, 0) + '<span class="tile-unit">°C</span>', 'Desinf. Soll', 'warn',
        null, '🧹', { pct: gPct(dhw.disinfection_temp, 30, 75), color: 'var(--orange)' });

    tt += tileT(F(s.outdoor_temp, 1) + '<span class="tile-unit">°C</span>', 'Außen', 'info',
        pv.outdoor_temp != null ? F(pv.outdoor_temp, 1) + '°C' : null, '🌤️',
        { pct: gPct(s.outdoor_temp, -10, 40), color: 'var(--accent)' });

    if (today.temp_min != null || today.temp_max != null) {
        tt += tile(F(today.temp_min, 1) + ' / ' + F(today.temp_max, 1) + '<span class="tile-unit">°C</span>',
            'Heute Min / Max', '', null, '📊',
            { pct: gPct(today.temp_max, -10, 40), color: 'var(--heat)' });
    }
    document.getElementById('tempTiles').innerHTML = tt;
}

function _renderDetails(b, s, dhw, gas, con, err, th) {
    function dt(lbl, val, gauge) {
        var h = '<div class="dtile" title="' + lbl + ': ' + val + '"><div class="dtile-lbl">' + lbl + '</div><div class="dtile-val">' + val + '</div>';
        if (gauge) h += '<div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill" style="width:' + Math.min(100, gauge.pct) + '%;background:' + (gauge.color || 'var(--accent)') + '"></div></div></div>';
        return h + '</div>';
    }
    function ds(title, id) { return '</div><div class="dsection" onclick="toggleDGroup(\'' + id + '\')">' + title + ' ▾</div><div class="dgroup" id="dg-' + id + '">'; }

    var dg = '<div class="dtiles"><div class="dgroup">';
    var errB = err.boiler || {}, errT = err.thermostat || {};
    if (errB.code || errT.code) {
        dg += ds('⚠️ Fehler / Service', 'err');
        if (errB.code) dg += dt('Kessel-Fehler', errB.description || errB.code) + dt('Code', errB.code);
        if (errT.code) dg += dt('Thermostat-Fehler', errT.description || errT.code) + dt('Code', errT.code);
        dg += dt('Fehler gesamt', err.count || 0);
    }
    dg += ds('🔧 Kessel', 'kessel');
    dg += dt('Servicecode', (b.service_code || '–') + ' (' + F(b.service_code_number) + ')');
    dg += dt('Wartung', b.maintenance_date || '–');
    dg += dt('Flammenstrom', F(b.flame_current, 1) + ' µA', b.flame_current > 0 ? { pct: Math.min(100, b.flame_current / 15 * 100), color: 'var(--gas)' } : null);
    dg += dt('Nennleistung', F(b.nominal_power_kw, 0) + ' kW');
    dg += dt('Akt. Leistung', F(b.current_power_kw, 1) + ' kW', { pct: b.nominal_power_kw ? (b.current_power_kw || 0) / b.nominal_power_kw * 100 : 0, color: 'var(--heat)' });
    dg += dt('Pumpe Modus', b.pump_mode || '–');
    dg += dt('Pumpe Min/Max', F(b.pump_min) + '% / ' + F(b.pump_max) + '%');
    dg += dt('Heizung', bL(b.heating_enabled));
    dg += dt('Heizkurve', bL(s.curve_on));
    dg += dt('Sommertemp', F(s.summer_temp, 0) + '°C');
    dg += dt('Frostschutz', bL(s.frost_mode) + ' ' + F(s.frost_temp, 0) + '°C');

    dg += ds('💧 Warmwasser', 'ww');
    dg += dt('Komfort', dhw.comfort || '–');
    dg += dt('Speichertyp', dhw.storage_type || '–');
    dg += dt('Vorlauf-Offset', F(dhw.flowtempoffset, 0) + '°C');

    if (gas) {
        dg += ds('⛽ Gaszähler', 'gas');
        dg += dt('Zählerstand', F(gas.display_m3, 3) + ' m³');
        dg += dt('Seit ESP-Install', F(gas.total_m3, 3) + ' m³');
        dg += dt('Zeitstempel', gas.timestamp || '–');
    }

    dg += ds('📊 Energie kumulativ', 'energy');
    var eMax = con.energy_total_kwh || 1;
    dg += dt('Gesamt', F(con.energy_total_kwh, 2) + ' kWh', { pct: 100, color: 'var(--gas)' });
    dg += dt('Heizung', F(con.energy_heat_kwh, 2) + ' kWh', { pct: eMax > 0 ? con.energy_heat_kwh / eMax * 100 : 0, color: 'var(--heat)' });
    dg += dt('Warmwasser', F(con.energy_dhw_kwh, 2) + ' kWh', { pct: eMax > 0 ? con.energy_dhw_kwh / eMax * 100 : 0, color: 'var(--dhw)' });

    if (th) {
        var hc1 = th.hc1 || {}, wwk = th.wwk || {};
        dg += ds('🌡️ Thermostat RC310', 'therm');
        dg += dt('Datum', th.datetime || '–');
        dg += dt('Gedämpfte Außen', F(th.damped_outdoor_temp, 1) + '°C');
        dg += dt('Gebäudetyp', th.building || '–');

        dg += ds('🏠 Heizkreis 1', 'hk1');
        dg += dt('Betriebsart', (hc1.mode || '–') + ' / ' + (hc1.modetype || ''));
        dg += dt('Raumtemp Soll', F(hc1.seltemp, 0) + '°C');
        dg += dt('Vorlauf berechnet', F(hc1.targetflowtemp, 0) + '°C');
        dg += dt('Vorlauf Min/Max', F(hc1.minflowtemp, 0) + ' / ' + F(hc1.maxflowtemp, 0) + '°C');
        dg += dt('Heizungstyp', hc1.heatingtype || '–');
        dg += dt('Sommerbetrieb', hc1.summermode || '–');
        dg += dt('Steuermodus', hc1.controlmode || '–');

        dg += ds('💧 WWK Thermostat', 'wwk');
        dg += dt('Betriebsart', wwk.mode || '–');
        dg += dt('Solltemp', F(wwk.settemp, 0) + '°C');
        dg += dt('Desinfektion', (wwk.disinfectday || '–') + ' · ' + F(wwk.disinfecttime, 0) + ' min');
    }
    dg += '</div></div>';
    document.getElementById('detailGrid').innerHTML = dg;
}


function _renderStatusBanner(err) {
    var el = document.getElementById('statusBanner');
    if (!el) return;
    var errB = err.boiler || {}, errT = err.thermostat || {};
    if (errB.code || errT.code) {
        var msg = '⚠️ ';
        if (errB.code) msg += 'Kessel: ' + (errB.description || errB.code);
        if (errB.code && errT.code) msg += ' · ';
        if (errT.code) msg += 'Thermostat: ' + (errT.description || errT.code);
        el.style.color = 'var(--heat)';
        el.style.fontSize = '.9rem';
        el.style.fontWeight = '600';
        el.innerHTML = msg;
    } else {
        el.style.color = 'var(--muted)';
        el.style.fontSize = '.75rem';
        el.style.fontWeight = 'normal';
        el.innerHTML = '✅ Heizungsanlage läuft und arbeitet einwandfrei';
    }
}

function _renderProgressBar(d) {
    var el = document.getElementById('progressBar');
    if (!el) return;
    var interval = 60;
    var maxCycles = Math.floor(24 * 3600 / interval);
    var now = new Date();
    var startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var expectedCycles = Math.floor((now - startOfDay) / 1000 / interval);

    /* Echte Zyklen aus API, Fallback auf theoretische wenn nach Restart */
    var cycle = d.cycle_count || 0;
    var isEstimate = !d.cycle_count;
    if (!isEstimate && cycle < expectedCycles / 2) {
        /* Nach Restart: theoretische Werte verwenden */
        cycle = expectedCycles;
        isEstimate = true;
    }
    if (isEstimate) cycle = expectedCycles;

    var pct = maxCycles > 0 ? Math.min(100, cycle / maxCycles * 100) : 0;
    /* Health: Zyklen vs. erwartete seit Start (nicht seit Mitternacht) */
    var health;
    if (isEstimate) {
        health = 100;
    } else if (cycle < 60 || cycle < expectedCycles * 0.4) {
        /* Anlaufphase oder nach Restart: noch nicht genug Daten */
        health = 100;
    } else {
        health = expectedCycles > 0 ? Math.round(cycle / expectedCycles * 100) : 100;
    }
    var color = health >= 95 ? 'var(--green)' : health >= 80 ? 'var(--orange)' : 'var(--heat)';

    /* Warnung wenn Zyklen nicht stimmen — erst nach 10 Min Anlaufzeit */
    var warn = '';
    if (!isEstimate && health < 90 && expectedCycles > 60) {
        warn = ' · <span style="color:var(--heat)">⚠️ ' + (100 - health) + '% Ausfälle</span>';
    }
    var label = isEstimate ? '~' + cycle : '' + cycle;

    el.innerHTML = '<div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-bottom:3px">' +
        '<span>0:00</span><span>Zyklen: ' + label + ' / ' + maxCycles + ' (' + health + '%)' + warn + '</span><span>24:00</span></div>' +
        '<div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden">' +
        '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:3px;transition:width 1s"></div></div>';
}


function _renderInfoRow(d, b, err, th, con, gas) {
    var el = document.getElementById('infoRow');
    if (!el) return;
    var hc1 = th && th.hc1 ? th.hc1 : {};
    var ir = '';

    /* Installiert seit (berechne zuerst für Gauge) */
    var installed = d.config_installed || '';
    var days = '–';
    var installedDays = 0;
    if (installed) {
        var inst = new Date(installed);
        if (!isNaN(inst)) { installedDays = Math.floor((new Date() - inst) / 86400000); days = installedDays + ' Tage'; }
    }

    /* Fehler: aktuell + gesamt */
    var errCount = err.count || 0;
    var errActive = (err.boiler && err.boiler.code ? 1 : 0) + (err.thermostat && err.thermostat.code ? 1 : 0);
    var errLast = (err.boiler && err.boiler.date) ? err.boiler.date : '–';
    ir += tile(errActive + '', 'Aktuelle Fehler', errActive > 0 ? 'err' : 'ok', 'Gesamt: ' + errCount + (errActive > 0 ? ' · Letzter: ' + errLast : ' · Keine aktiven'), errActive > 0 ? '⚠️' : '✅');

    /* Heizbetrieb Sommer/Winter */
    var season = hc1.summermode || '–';
    ir += tile(season, 'Heizbetrieb', season === 'Winter' ? 'heat' : 'dhw', null, season === 'Winter' ? '❄️' : '☀️');

    /* Betriebszeiten aus consumption + Gauge relativ zu Installationszeit */
    var burnerMin = con.burner_runtime_min || 0;
    var heatMin = con.heating_runtime_min || 0;
    var burnerH = burnerMin ? F(burnerMin / 60, 0) + 'h' : '–';
    var heatH = heatMin ? F(heatMin / 60, 0) + 'h' : '–';
    var starts = con.burner_starts || '–';
    /* Gauge: Brennerlaufzeit vs. Installationszeit */
    var installedHours = installedDays * 24;
    var burnerPct = installedHours > 0 ? Math.round(burnerMin / 60 / installedHours * 100) : 0;
    ir += tile(burnerH, 'Brenner Laufzeit', '', 'Heizung ' + heatH + ' · ' + starts + ' Starts · ' + burnerPct + '% Auslastung', '⏱️', burnerMin > 0 ? { pct: burnerPct, color: 'var(--heat)' } : null);

    ir += tile(days, 'Installiert seit', '', installed ? installed.split(' ')[0] : '', '📅');

    /* Anteil Heizung/WW */
    var totalKwh = con.energy_total_kwh || 1;
    var heatPct = totalKwh > 0 ? Math.round((con.energy_heat_kwh || 0) / totalKwh * 100) : 0;
    var dhwPct = 100 - heatPct;
    ir += tile(heatPct + '% / ' + dhwPct + '%', 'Anteil Heizung/Boiler', '', F(con.energy_heat_kwh, 0) + ' / ' + F(con.energy_dhw_kwh, 0) + ' kWh', '📊', null, null, stackedGauge([{ val: heatPct, color: 'var(--heat)', label: 'Heizung' }, { val: dhwPct, color: 'var(--dhw)', label: 'WW' }]));

    /* Status EMS-ESP — online wenn Daten vorhanden */
    var emsOk = d.timestamp && b.flow_temp != null;
    ir += tile(emsOk ? 'Online' : 'Offline', 'EMS-ESP', emsOk ? 'ok' : 'err', emsOk ? 'Daten aktuell' : 'Keine Daten', '📡');

    /* Status Boiler */
    var boilerOk = b.flow_temp != null;
    ir += tile(boilerOk ? 'OK' : '?', 'Boiler', boilerOk ? 'ok' : 'warn', boilerOk ? F(b.flow_temp, 1) + '°C' : 'Keine Daten', '🔥');

    /* Status Thermostat */
    var thermOk = th && th.hc1 && th.hc1.mode;
    ir += tile(thermOk ? 'OK' : '?', 'Thermostat', thermOk ? 'ok' : 'warn', thermOk ? (th.hc1.mode + ' / ' + (th.hc1.modetype || '')) : 'Keine Daten', '🌡️');

    /* Status Gaszähler */
    var gasOk = gas && gas.display_m3;
    ir += tile(gasOk ? 'OK' : '?', 'Gaszähler', gasOk ? 'ok' : 'warn', gasOk ? F(gas.display_m3, 1) + ' m³' : 'Keine Daten', '⛽');

    el.innerHTML = '<div class="tiles" style="width:100%;margin:0">' + ir + '</div>';
}
