// components/HeizungStatusFooter.js
export class HeizungStatusFooter {
    render() {
        return `
        <div id="status-footer-container">
            <!-- Das Status-Banner unter den Kacheln -->
            <div id="status-banner">Lade Anlagenstatus...</div>

            <!-- Die Tages-Fortschrittsanzeige -->
            <div id="day-progress-container">
                <div class="progress-labels">
                    <span>0:00</span>
                    <span id="progress-cycle-text">Tagesverlauf: --:-- (--%) · Zyklen: --</span>
                    <span>24:00</span>
                </div>
                <div class="progress-bar-bg">
                    <div id="progress-bar-fill" class="progress-bar-fill"></div>
                </div>
            </div>
        </div>
        `;
    }

    update(data, container) {
        if (!container || !data) return;

        // 1. Update für das ausformulierte Status-Banner (Gemappt auf data.errors.count)
        const banner = container.querySelector('#status-banner');
        if (banner) {
            const errCount = data.errors?.count || 0;
            if (errCount > 0) {
                banner.textContent = `❌ Achtung: Störung an der Heizungsanlage aktiv (${errCount} Fehler)!`;
                banner.className = 'banner-error';
            } else {
                banner.textContent = `✅ Heizungsanlage läuft und arbeitet einwandfrei`;
                banner.className = 'banner-ok';
            }
        }

        // 2. Update für den Zeit- / Zyklus-Balken basierend auf dem Server-Zeitstempel
        const cycText = container.querySelector('#progress-cycle-text');
        const cycBar = container.querySelector('#progress-bar-fill');

        if (cycText && cycBar) {
            let prozent = 0;
            let labelText = '';

            // Server-Zeitstempel parsen (z.B. "2026-06-19T08:31:03.891206+02:00")
            const serverZeit = data.timestamp ? new Date(data.timestamp) : new Date();

            // Sicherstellen, dass das Datum valide geparst wurde
            if (!isNaN(serverZeit.getTime())) {
                const stunden = serverZeit.getHours();
                const minuten = serverZeit.getMinutes();
                const minutenSeitMitternacht = (stunden * 60) + minuten;

                prozent = (minutenSeitMitternacht / 1440) * 100;

                // Formatiere Stunden und Minuten mit führenden Nullen
                const timeString = `${stunden.toString().padStart(2, '0')}:${minuten.toString().padStart(2, '0')}`;
                const gesamtZyklen = data.cycle_count || 0;

                labelText = `Tagesverlauf: ${timeString} (${Math.round(prozent)}%) · Gesamt-Zyklen: ${gesamtZyklen}`;
            } else {
                labelText = `Tagesverlauf: --:-- · Zyklen: ${data.cycle_count || '--'}`;
            }

            cycText.textContent = labelText;
            cycBar.style.width = `${prozent}%`;
        }
    }
}
