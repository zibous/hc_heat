/* dateselector.js – Dropdown Period Selector (hc_smet Style) */
/* Relative periods are ALWAYS recalculated on page load. */
'use strict';

var DS_PERIODS = {
    'Heute': 'today',
    'Gestern': 'gestern',
    'Diese Woche': 'woche',
    'Letzte 7 Tage': '7tage',
    'Letzte 30 Tage': '30tage',
    'Dieser Monat': 'monat'
};

var DS_STORAGE_KEY = 'haco-period-label';

function _dsCalcRange(key) {
    var now = new Date();
    var f = new Date(), t = new Date();
    f.setHours(0, 0, 0, 0);
    t.setHours(23, 59, 59, 999);

    switch (key) {
        case 'today': break;
        case 'gestern':
            f.setDate(now.getDate() - 1);
            t.setDate(now.getDate() - 1);
            break;
        case 'woche':
            var day = now.getDay();
            f.setDate(now.getDate() - day + (day === 0 ? -6 : 1));
            break;
        case '7tage': f.setDate(now.getDate() - 6); break;
        case '30tage': f.setDate(now.getDate() - 29); break;
        case 'monat': f.setDate(1); break;
    }
    return { from: _dsFmtDate(f), to: _dsFmtDate(t) };
}

function _dsFmtDate(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

/**
 * Initialize the dropdown period selector.
 * @param {HTMLElement} container - The element to place the selector in
 * @param {Function} onPeriodChange - Callback: ({period, params}) => void
 * @returns {Function} refresh - Call to re-trigger current period
 */
function initDateSelector(container, onPeriodChange) {
    var savedLabel = localStorage.getItem(DS_STORAGE_KEY) || 'Heute';

    if (DS_PERIODS[savedLabel]) {
        /* OK */
    } else if (!savedLabel.match(/^Jahr /) && savedLabel !== 'Individuell') {
        savedLabel = 'Heute';
    }

    var currentYear = new Date().getFullYear();
    var yearOptions = '';
    for (var y = currentYear; y >= 2026; y--) {
        yearOptions += '<option value="' + y + '">Jahr ' + y + '</option>';
    }

    /* Inject styles */
    if (!document.getElementById('ds-styles')) {
        var style = document.createElement('style');
        style.id = 'ds-styles';
        style.textContent =
            '.ds-wrap { position: relative; display: inline-flex; align-items: center; gap: 6px; }' +
            '.ds-label { font-size: 1.0rem; color: var(--muted); text-transform: uppercase; }' +
            '.ds-btn { padding: 6px 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: .82rem; font-weight: 500; }' +
            '.ds-btn::after { content: " \\25BE"; opacity: .6; }' +
            '.ds-dropdown { position: absolute; top: calc(100% + 6px); left: 0; min-width: 220px; border-radius: 12px; padding: 6px; z-index: 9999; max-height: 420px; overflow-y: auto; backdrop-filter: blur(30px) saturate(160%); -webkit-backdrop-filter: blur(30px) saturate(160%); box-shadow: 0 16px 48px rgba(0,0,0,.35); background: rgba(13, 20, 38, 0.94); border: 1px solid rgba(255,255,255,.12); }' +
            'body.light .ds-dropdown { background: rgba(255,255,255,.92); border: 1px solid rgba(0,0,0,.08); box-shadow: 0 16px 48px rgba(0,0,0,.15); }' +
            '.ds-dropdown.hidden { display: none; }' +
            '.ds-section { font-size: .68rem; font-weight: 700; color: var(--muted); padding: 8px 12px 2px; text-transform: uppercase; letter-spacing: .5px; }' +
            '.ds-item { padding: 8px 12px; border-radius: 8px; font-size: .82rem; color: var(--text); cursor: pointer; }' +
            '.ds-item:hover { background: rgba(128,128,128,.12); }' +
            '.ds-item.active { background: var(--accent); color: #fff; }' +
            '.ds-select { width: calc(100% - 24px); margin: 4px 12px; padding: 6px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text); font-size: .82rem; }' +
            '.ds-custom { padding: 8px 12px; display: none; }' +
            '.ds-custom.show { display: flex; flex-direction: column; gap: 6px; }' +
            '.ds-custom input { padding: 5px 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text); font-size: .82rem; }' +
            '.ds-custom button { padding: 6px; border-radius: 6px; border: none; background: var(--accent); color: #fff; font-size: .82rem; cursor: pointer; font-weight: 600; }';
        document.head.appendChild(style);
    }

    /* Build HTML */
    var wrap = document.createElement('div');
    wrap.className = 'ds-wrap';
    wrap.innerHTML =
        '<span class="ds-label">Zeitraum</span>' +
        '<button class="ds-btn" id="dsBtn">' + savedLabel + '</button>' +
        '<div class="ds-dropdown hidden" id="dsDrop">' +
            '<div class="ds-section">Zeitraum</div>' +
            '<div class="ds-item" data-key="today">Heute</div>' +
            '<div class="ds-item" data-key="gestern">Gestern</div>' +
            '<div class="ds-item" data-key="woche">Diese Woche</div>' +
            '<div class="ds-item" data-key="7tage">Letzte 7 Tage</div>' +
            '<div class="ds-item" data-key="30tage">Letzte 30 Tage</div>' +
            '<div class="ds-item" data-key="monat">Dieser Monat</div>' +
            '<div class="ds-section">Archiv</div>' +
            '<select class="ds-select" id="dsYear">' +
                '<option value="">Jahr ausw\u00E4hlen\u2026</option>' +
                yearOptions +
            '</select>' +
            '<div class="ds-section" style="cursor:pointer" id="dsCustomToggle">Benutzerdefiniert\u2026</div>' +
            '<div class="ds-custom" id="dsCustom">' +
                '<input type="date" id="dsFrom">' +
                '<input type="date" id="dsTo">' +
                '<button id="dsApply">Anwenden</button>' +
            '</div>' +
        '</div>';

    container.appendChild(wrap);

    var btn = wrap.querySelector('#dsBtn');
    var drop = wrap.querySelector('#dsDrop');
    var yearSel = wrap.querySelector('#dsYear');
    var customToggle = wrap.querySelector('#dsCustomToggle');
    var customBox = wrap.querySelector('#dsCustom');
    var fromInput = wrap.querySelector('#dsFrom');
    var toInput = wrap.querySelector('#dsTo');
    var applyBtn = wrap.querySelector('#dsApply');

    /* Toggle dropdown */
    btn.addEventListener('click', function (e) { e.stopPropagation(); drop.classList.toggle('hidden'); });
    document.addEventListener('click', function () { drop.classList.add('hidden'); });
    drop.addEventListener('click', function (e) { e.stopPropagation(); });

    /* Fire period change */
    function fire(label) {
        savedLabel = label;
        localStorage.setItem(DS_STORAGE_KEY, label);
        btn.textContent = label;
        drop.classList.add('hidden');

        /* Highlight active */
        drop.querySelectorAll('.ds-item').forEach(function (el) {
            var itemLabel = el.textContent.trim();
            el.classList.toggle('active', itemLabel === label);
        });

        if (DS_PERIODS[label]) {
            var key = DS_PERIODS[label];
            var range = _dsCalcRange(key);
            if (key === 'today' || key === 'gestern') {
                onPeriodChange({ period: 'today', params: { date: range.from } });
            } else {
                onPeriodChange({ period: 'day', params: { from: range.from, to: range.to } });
            }
        } else if (label.match(/^Jahr /)) {
            var yr = label.replace('Jahr ', '');
            onPeriodChange({ period: 'month', params: { from: yr + '-01-01', to: yr + '-12-31' } });
        } else if (label === 'Individuell') {
            var f = fromInput.value;
            var t = toInput.value;
            if (f && t) {
                onPeriodChange({ period: 'day', params: { from: f, to: t } });
            }
        }
    }

    /* Item clicks */
    drop.querySelectorAll('.ds-item').forEach(function (item) {
        item.addEventListener('click', function () {
            var key = item.dataset.key;
            var labels = { today: 'Heute', gestern: 'Gestern', woche: 'Diese Woche', '7tage': 'Letzte 7 Tage', '30tage': 'Letzte 30 Tage', monat: 'Dieser Monat' };
            fire(labels[key] || key);
        });
    });

    /* Year select */
    yearSel.addEventListener('change', function () {
        if (yearSel.value) fire('Jahr ' + yearSel.value);
    });

    /* Custom toggle */
    customToggle.addEventListener('click', function () { customBox.classList.toggle('show'); });

    /* Custom apply */
    applyBtn.addEventListener('click', function () {
        if (fromInput.value && toInput.value) fire('Individuell');
    });

    /* Initial fire */
    if (savedLabel.match(/^Jahr /)) {
        yearSel.value = savedLabel.replace('Jahr ', '');
    }
    fire(savedLabel);

    /* Return refresh function */
    return function () { fire(savedLabel); };
}
