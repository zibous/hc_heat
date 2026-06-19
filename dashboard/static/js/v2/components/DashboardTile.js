// components/DashboardTile.js
export class DashboardTile {
    /**
     * @param {Object} config - Konfiguration der Kachel
     * @param {string} config.id - Eindeutige ID im DOM
     * @param {string} config.title - Label oben links
     * @param {string} config.icon - Emoji, Icon oder SVG oben rechts
     * @param {function} config.renderContent - Funktion, die das innere HTML liefert
     */
    constructor(config) {
        this.id = config.id;
        this.title = config.title;
        this.icon = config.icon || '';
        this.renderContent = config.renderContent;
    }

    /**
     * Erzeugt die äußere Kachel-Hülle für den initialen Seitenaufbau
     * @param {Object} initialData - Optionale Startdaten, falls vorhanden
     */
    render(initialData = {}) {
        return `
            <div class="tile" id="tile-${this.id}">
                <div class="tile-head">
                    <span class="tile-head-lbl">${this.title}</span>
                    <span class="tile-head-icon">${this.icon}</span>
                </div>
                <div class="tile-body-content">
                    ${this.renderContent(initialData)}
                </div>
            </div>
        `;
    }

    /**
     * Aktualisiert gezielt nur den inneren Inhalt dieser einen Kachel im DOM
     * @param {Object} data - Das rohe oder gemappte JSON-Datenobjekt vom Server
     */
    update(data) {
        // Sucht das Element im DOM frisch heraus (verhindert Speicher-Leaks und tote Referenzen)
        const element = document.getElementById(`tile-${this.id}`);

        if (element) {
            const bodyContent = element.querySelector('.tile-body-content');
            if (bodyContent) {
                // Führt die Render-Funktion mit den neuen API-Daten aus
                bodyContent.innerHTML = this.renderContent(data || {});
            }
        }
    }
}
