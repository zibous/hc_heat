// components/Tile.js
export class Tile {
    constructor({ id, title, iconPath }) {
        this.id = id;
        this.title = title;
        this.iconPath = iconPath;
    }

    render(val, sub, statusClass = '', extra = null) {
        let extraHtml = '';

        if (extra) {
            if (extra.type === 'stacked') {
                const segs = extra.widths.map((w, i) => `<div class="seg ${extra.classes[i]}" style="width:${w}%"></div>`).join('');
                extraHtml = `<div class="tile-gauge-stacked">${segs}</div>`;
            } else if (extra.type === 'normal') {
                extraHtml = `<div class="tile-gauge"><div class="tile-gauge-bar"><div class="tile-gauge-fill ${extra.class}" style="width:${extra.width}%"></div></div></div>`;
            } else if (extra.type === 'segments') {
                const segs = extra.list.map(s => `<div class="mode-seg ${s.active ? 'active ' + s.class : ''}" title="${s.title}"></div>`).join('');
                extraHtml = `<div class="mode-segments">${segs}</div>`;
            } else if (extra.type === 'sparkline') {
                // Absicherung für leere Arrays, um Division durch Null zu verhindern
                const len = extra.values.length > 1 ? extra.values.length - 1 : 1;
                const points = extra.values.map((v, i) => `${(i / len) * 180},${25 - (v * 20)}`).join(' ');
                extraHtml = `
                    <div class="tile-sparkline">
                        <svg viewBox="0 0 180 25" style="width:100%; height:25px;">
                            <polyline fill="none" stroke="${extra.color || 'var(--accent, #3b82f6)'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="${points}"/>
                        </svg>
                    </div>`;
            }
            // === NEU: 3. Split-Anzeige für Anteile/Vergleiche ===
            else if (extra.type === 'split') {
                // Optimierung: Nutzen der Variablen aus deinem Unified Theme für perfekte Farbkonformität
                return `
                    <div id="${this.id}" class="tile ${statusClass}">
                        <div class="tile-head">
                            <span class="tile-head-lbl">${this.title}</span>
                            <span class="tile-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${this.iconPath}</svg>
                            </span>
                        </div>
                        <div class="tile-split-container">
                            <div class="tile-split-side">
                                <div class="tile-val-mini" style="color: var(--red, #ef4444)">${extra.left.val}</div>
                                <div class="tile-sub">${extra.left.sub}</div>
                            </div>
                            <div class="tile-split-divider"></div>
                            <div class="tile-split-side">
                                <div class="tile-val-mini" style="color: var(--accent, #3b82f6)">${extra.right.val}</div>
                                <div class="tile-sub">${extra.right.sub}</div>
                            </div>
                        </div>
                        <div class="tile-gauge-stacked" style="margin-top: 12px;">
                            <div class="seg style-heat" style="width:${extra.left.percent}%"></div>
                            <div class="seg style-ww" style="width:${extra.right.percent}%"></div>
                        </div>
                    </div>
                `;
            }
        }

        return `
            <div id="${this.id}" class="tile ${statusClass}">
                <div class="tile-head">
                    <span class="tile-head-lbl">${this.title}</span>
                    <span class="tile-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${this.iconPath}</svg>
                    </span>
                </div>
                <div class="tile-val">${val}</div>
                <div class="tile-sub">${sub}</div>
                ${extraHtml}
            </div>
        `;
    }
}
