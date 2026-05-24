"""History Writer: Schreibt Zyklusdaten als CSV in data/history/.

Pro Woche eine Datei: YYYY-WNN.csv (z.B. 2026-W18.csv).
Neue Einträge werden angehängt. Header wird nur bei neuer Datei geschrieben.

Konfiguration über .env:
    SAVE_HISTORY=true       # History aktivieren
    HISTORY_DIR=./data/history  # Verzeichnis
    HISTORY_KEEP_WEEKS=8    # Alte Dateien nach N Wochen löschen (0=nie)
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hc_haco2.history_writer")

# CSV-Spalten – alle relevanten Daten für Replay
COLUMNS = [
    "ts",
    "mode",
    "outdoor_temp",
    "flow_temp",
    "flow_set_temp",
    "target_flow_temp",
    "dhw_temp",
    "dhw_set_temp",
    "burner_active",
    "burner_power",
    "pump_active",
    "pump_modulation",
    "energy_total_kwh",
    "energy_heat_kwh",
    "energy_dhw_kwh",
    "gas_display_m3",
]


class HistoryWriter:
    """Schreibt Heizungsdaten als wöchentliche CSV-Dateien."""

    def __init__(
        self,
        history_dir: str = "./data/history",
        enabled: bool = True,
        keep_weeks: int = 8,
    ):
        self.enabled = enabled
        self.keep_weeks = keep_weeks
        self.history_dir = Path(history_dir)
        self._current_file: Optional[str] = None
        self._writer: Optional[csv.writer] = None
        self._fh = None

        if self.enabled:
            self.history_dir.mkdir(parents=True, exist_ok=True)
            logger.info("History Writer aktiv: %s", self.history_dir)

    def _week_filename(self, ts: datetime) -> str:
        """Dateiname: YYYY-WNN.csv"""
        year, week, _ = ts.isocalendar()
        return f"{year}-W{week:02d}.csv"

    def _ensure_file(self, filename: str) -> None:
        """Öffnet die CSV-Datei, schreibt Header falls neu."""
        if self._current_file == filename and self._fh is not None:
            return

        # Alte Datei schließen
        self.close()

        filepath = self.history_dir / filename
        is_new = not filepath.exists() or filepath.stat().st_size == 0

        self._fh = open(filepath, "a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fh, delimiter=";")
        self._current_file = filename

        if is_new:
            self._writer.writerow(COLUMNS)
            self._fh.flush()
            logger.info("Neue History-Datei: %s", filename)

    def write(self, **kwargs) -> None:
        """Schreibt eine Zeile in die aktuelle Wochen-CSV."""
        if not self.enabled:
            return

        try:
            ts = kwargs.get("ts", "")
            if isinstance(ts, str) and ts:
                dt = datetime.fromisoformat(ts)
            else:
                dt = datetime.now()

            filename = self._week_filename(dt)
            self._ensure_file(filename)

            row = [kwargs.get(col, "") for col in COLUMNS]
            self._writer.writerow(row)
            self._fh.flush()

        except Exception as e:
            logger.error("History write fehlgeschlagen: %s", e)

    def cleanup(self) -> int:
        """Löscht History-Dateien älter als keep_weeks Wochen.

        Returns:
            Anzahl gelöschter Dateien.
        """
        if not self.enabled or self.keep_weeks <= 0:
            return 0

        now = datetime.now()
        year_now, week_now, _ = now.isocalendar()
        deleted = 0

        for f in sorted(self.history_dir.glob("*.csv")):
            try:
                # Parse YYYY-WNN.csv
                parts = f.stem.split("-W")
                if len(parts) != 2:
                    continue
                f_year = int(parts[0])
                f_week = int(parts[1])

                # Wochen-Differenz berechnen
                weeks_diff = (year_now - f_year) * 52 + (week_now - f_week)
                if weeks_diff > self.keep_weeks:
                    f.unlink()
                    logger.info("History gelöscht: %s (%d Wochen alt)", f.name, weeks_diff)
                    deleted += 1
            except (ValueError, IndexError):
                continue

        return deleted

    def close(self) -> None:
        """Schließt die aktuelle Datei."""
        if self._fh:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None
            self._writer = None
            self._current_file = None
