"""Historie-Provider: Liest Zeitreihen aus SQLite für das Dashboard.

Im Produktivbetrieb werden Daten bei jedem Zyklus in die DB geschrieben.
Im Simulate-Modus sind die Daten bereits in der DB.
"""

import logging
from typing import Optional

from .db_manager import DBManager

logger = logging.getLogger(" hc_heat.history_buffer")


class HistoryBuffer:
    """Liest Temperatur-Historie aus der SQLite-Datenbank."""

    def __init__(self, db: Optional[DBManager] = None):
        self.db = db or DBManager()

    def get_all(self) -> list[dict]:
        """Alle Datenpunkte (für kleine DBs / Simulate)."""
        rows = self.db.query_all()
        return [self._to_point(r) for r in rows]

    def get_last_hours(self, hours: int = 24) -> list[dict]:
        """Letzte N Stunden."""
        rows = self.db.query_last(hours)
        return [self._to_point(r) for r in rows]

    def get_range(self, start: str, end: str) -> list[dict]:
        """Zeitraum (ISO-Strings)."""
        rows = self.db.query_range(start, end)
        return [self._to_point(r) for r in rows]

    @staticmethod
    def _to_point(row: dict) -> dict:
        """Konvertiert DB-Zeile in Dashboard-Format."""
        return {
            "ts": row.get("ts"),
            "outdoor": row.get("outdoor_temp"),
            "flow": row.get("flow_temp"),
            "flow_set": row.get("flow_set_temp"),
            "target_flow": row.get("target_flow_temp"),
            "dhw": row.get("dhw_temp"),
            "dhw_set": row.get("dhw_set_temp"),
            "burner": bool(row.get("burner_active")),
            "power": row.get("burner_power"),
            "mode": row.get("mode"),
        }
