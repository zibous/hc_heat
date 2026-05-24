"""SQLite Datenbank-Manager für Heizungsdaten.

Speichert Messwerte als Zeitreihe. Eine Zeile pro Zyklus.
Leichtgewichtig, kein ORM.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from config.app_config import BASE_DIR

logger = logging.getLogger("hc_haco2.db")

DB_PATH = BASE_DIR / "data" / "heating.db"
DB_PATH_SIM = BASE_DIR / "data" / "heating_sim.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    mode TEXT,
    outdoor_temp REAL,
    flow_temp REAL,
    flow_set_temp REAL,
    target_flow_temp REAL,
    dhw_temp REAL,
    dhw_set_temp REAL,
    burner_active INTEGER,
    burner_power INTEGER,
    pump_active INTEGER,
    pump_modulation INTEGER,
    energy_total_kwh REAL,
    energy_heat_kwh REAL,
    energy_dhw_kwh REAL,
    gas_display_m3 REAL,
    gas_total_m3 REAL,
    burner_starts INTEGER,
    burner_runtime_min INTEGER,
    heating_starts INTEGER,
    heating_runtime_min INTEGER,
    lastcode_boiler TEXT,
    lastcode_thermostat TEXT
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ts ON measurements(ts);
"""


class DBManager:
    """SQLite Manager für Heizungsdaten."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(CREATE_TABLE)
            conn.execute(CREATE_INDEX)
            conn.commit()
        logger.debug("DB initialisiert: %s", self.db_path)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def insert(self, **kwargs: object) -> None:
        """Fügt eine Messung ein."""
        cols = [
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
            "gas_total_m3",
            "burner_starts",
            "burner_runtime_min",
            "heating_starts",
            "heating_runtime_min",
            "lastcode_boiler",
            "lastcode_thermostat",
        ]
        values = [kwargs.get(c) for c in cols]
        placeholders = ",".join(["?"] * len(cols))
        col_names = ",".join(cols)
        sql = f"INSERT INTO measurements ({col_names}) VALUES ({placeholders})"
        with self._conn() as conn:
            conn.execute(sql, values)
            conn.commit()

    def insert_many(self, rows: list[dict]) -> None:
        """Fügt mehrere Messungen auf einmal ein (schnell)."""
        if not rows:
            return
        cols = [
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
            "gas_total_m3",
            "burner_starts",
            "burner_runtime_min",
            "heating_starts",
            "heating_runtime_min",
            "lastcode_boiler",
            "lastcode_thermostat",
        ]
        placeholders = ",".join(["?"] * len(cols))
        col_names = ",".join(cols)
        sql = f"INSERT INTO measurements ({col_names}) VALUES ({placeholders})"
        with self._conn() as conn:
            conn.executemany(sql, [[r.get(c) for c in cols] for r in rows])
            conn.commit()

    def query_range(self, start: str, end: str) -> list[dict]:
        """Gibt Messungen in einem Zeitraum zurück (ISO-Strings)."""
        sql = "SELECT * FROM measurements WHERE ts >= ? AND ts <= ? ORDER BY ts"
        with self._conn() as conn:
            rows = conn.execute(sql, (start, end)).fetchall()
        return [dict(r) for r in rows]

    def query_last(self, hours: int = 24, max_points: int = 500) -> list[dict]:
        """Gibt die letzten N Stunden zurück, ausgedünnt auf max_points."""
        count_sql = """
            SELECT COUNT(*) FROM measurements
            WHERE ts >= (SELECT datetime(MAX(ts), ?) FROM measurements)
        """
        with self._conn() as conn:
            total = conn.execute(count_sql, (f"-{hours} hours",)).fetchone()[0]

        step = max(1, total // max_points)

        sql = """
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (ORDER BY ts) as rn
                FROM measurements
                WHERE ts >= (SELECT datetime(MAX(ts), ?) FROM measurements)
            ) WHERE rn % ? = 0 OR rn = 1
            ORDER BY ts
        """
        with self._conn() as conn:
            rows = conn.execute(sql, (f"-{hours} hours", step)).fetchall()
        return [dict(r) for r in rows]

    def query_all(self) -> list[dict]:
        """Gibt alle Messungen zurück."""
        sql = "SELECT * FROM measurements ORDER BY ts"
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]

    def query_daily(
        self, days: int = 14, from_date: str = "", to_date: str = ""
    ) -> list[dict]:
        """Aggregiert Verbrauch pro Zeiteinheit.

        days=1:    stündlich (24 Balken)
        days<=90:  täglich
        days>90:   monatlich
        from_date/to_date: expliziter Zeitraum (überschreibt days)
        """
        if from_date and to_date:
            return self._query_range_daily(from_date, to_date)
        if days <= 1:
            return self._query_hourly()
        if days > 90:
            return self._query_monthly(days)

        sql = """
            SELECT
                substr(ts, 1, 10) as day,
                MIN(energy_total_kwh) as e_start, MAX(energy_total_kwh) as e_end,
                MIN(energy_heat_kwh) as eh_start, MAX(energy_heat_kwh) as eh_end,
                MIN(energy_dhw_kwh) as ed_start, MAX(energy_dhw_kwh) as ed_end,
                MIN(gas_display_m3) as g_start, MAX(gas_display_m3) as g_end,
                SUM(CASE WHEN burner_active=1 THEN 1 ELSE 0 END) as burner_min
            FROM measurements
            GROUP BY substr(ts, 1, 10)
            ORDER BY day DESC
            LIMIT ?
        """
        with self._conn() as conn:
            rows = conn.execute(sql, (days,)).fetchall()
        result = []
        for r in reversed(rows):
            result.append(
                {
                    "day": r[0],
                    "energy_kwh": round((r[2] or 0) - (r[1] or 0), 2),
                    "heat_kwh": round((r[4] or 0) - (r[3] or 0), 2),
                    "dhw_kwh": round((r[6] or 0) - (r[5] or 0), 2),
                    "gas_m3": round((r[8] or 0) - (r[7] or 0), 3),
                    "burner_min": r[9] or 0,
                }
            )
        return result

    def _query_hourly(self) -> list[dict]:
        """Aggregiert Verbrauch pro Stunde für den letzten Tag."""
        sql = """
            WITH last_day AS (
                SELECT substr(ts, 1, 10) as day
                FROM measurements ORDER BY ts DESC LIMIT 1
            )
            SELECT
                substr(ts, 12, 2) as hour,
                MIN(energy_total_kwh), MAX(energy_total_kwh),
                MIN(energy_heat_kwh), MAX(energy_heat_kwh),
                MIN(energy_dhw_kwh), MAX(energy_dhw_kwh),
                MIN(gas_display_m3), MAX(gas_display_m3),
                SUM(CASE WHEN burner_active=1 THEN 1 ELSE 0 END)
            FROM measurements
            WHERE substr(ts, 1, 10) = (SELECT day FROM last_day)
            GROUP BY substr(ts, 12, 2)
            ORDER BY hour
        """
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
        result = []
        for r in rows:
            result.append(
                {
                    "day": r[0] + ":00",
                    "energy_kwh": round((r[2] or 0) - (r[1] or 0), 2),
                    "heat_kwh": round((r[4] or 0) - (r[3] or 0), 2),
                    "dhw_kwh": round((r[6] or 0) - (r[5] or 0), 2),
                    "gas_m3": round((r[8] or 0) - (r[7] or 0), 3),
                    "burner_min": r[9] or 0,
                }
            )
        return result

    def _query_range_daily(self, from_date: str, to_date: str) -> list[dict]:
        """Aggregiert Verbrauch pro Tag für einen expliziten Zeitraum."""
        sql = """
            SELECT
                substr(ts, 1, 10) as day,
                MIN(energy_total_kwh), MAX(energy_total_kwh),
                MIN(energy_heat_kwh), MAX(energy_heat_kwh),
                MIN(energy_dhw_kwh), MAX(energy_dhw_kwh),
                MIN(gas_display_m3), MAX(gas_display_m3),
                SUM(CASE WHEN burner_active=1 THEN 1 ELSE 0 END)
            FROM measurements
            WHERE substr(ts, 1, 10) >= ? AND substr(ts, 1, 10) <= ?
            GROUP BY substr(ts, 1, 10)
            ORDER BY day
        """
        with self._conn() as conn:
            rows = conn.execute(sql, (from_date, to_date)).fetchall()
        result = []
        for r in rows:
            result.append(
                {
                    "day": r[0],
                    "energy_kwh": round((r[2] or 0) - (r[1] or 0), 2),
                    "heat_kwh": round((r[4] or 0) - (r[3] or 0), 2),
                    "dhw_kwh": round((r[6] or 0) - (r[5] or 0), 2),
                    "gas_m3": round((r[8] or 0) - (r[7] or 0), 3),
                    "burner_min": r[9] or 0,
                }
            )
        return result

    def _query_monthly(self, days: int = 365) -> list[dict]:
        """Aggregiert Verbrauch pro Monat."""
        sql = """
            SELECT
                substr(ts, 1, 7) as month,
                MIN(energy_total_kwh), MAX(energy_total_kwh),
                MIN(energy_heat_kwh), MAX(energy_heat_kwh),
                MIN(energy_dhw_kwh), MAX(energy_dhw_kwh),
                MIN(gas_display_m3), MAX(gas_display_m3),
                SUM(CASE WHEN burner_active=1 THEN 1 ELSE 0 END)
            FROM measurements
            GROUP BY substr(ts, 1, 7)
            ORDER BY month DESC
            LIMIT 12
        """
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
        result = []
        for r in reversed(rows):
            result.append(
                {
                    "day": r[0],
                    "energy_kwh": round((r[2] or 0) - (r[1] or 0), 2),
                    "heat_kwh": round((r[4] or 0) - (r[3] or 0), 2),
                    "dhw_kwh": round((r[6] or 0) - (r[5] or 0), 2),
                    "gas_m3": round((r[8] or 0) - (r[7] or 0), 3),
                    "burner_min": r[9] or 0,
                }
            )
        return result

    def query_today_delta(self) -> dict:
        """Berechnet Verbrauch heute (Differenz erster/letzter Wert des Tages).

        Bestimmt 'heute' anhand des letzten Timestamps in der DB,
        nicht anhand der Systemzeit (funktioniert auch mit Simulate-Daten).
        """
        sql = """
            WITH today AS (
                SELECT substr(ts, 1, 10) as day
                FROM measurements ORDER BY ts DESC LIMIT 1
            )
            SELECT
                MIN(energy_total_kwh), MAX(energy_total_kwh),
                MIN(energy_heat_kwh), MAX(energy_heat_kwh),
                MIN(energy_dhw_kwh), MAX(energy_dhw_kwh),
                MIN(gas_display_m3), MAX(gas_display_m3),
                SUM(CASE WHEN burner_active=1 THEN 1 ELSE 0 END)
            FROM measurements
            WHERE substr(ts, 1, 10) = (SELECT day FROM today)
        """
        with self._conn() as conn:
            row = conn.execute(sql).fetchone()
        if not row or row[0] is None:
            return {
                "energy_kwh": 0,
                "heat_kwh": 0,
                "dhw_kwh": 0,
                "gas_m3": 0,
                "burner_min": 0,
            }
        return {
            "energy_kwh": round((row[1] or 0) - (row[0] or 0), 2),
            "heat_kwh": round((row[3] or 0) - (row[2] or 0), 2),
            "dhw_kwh": round((row[5] or 0) - (row[4] or 0), 2),
            "gas_m3": round((row[7] or 0) - (row[6] or 0), 3),
            "burner_min": row[8] or 0,
        }

    def clear(self) -> None:
        """Löscht alle Daten (für Simulate-Reset)."""
        with self._conn() as conn:
            conn.execute("DELETE FROM measurements")
            conn.commit()
        logger.info("DB geleert")

    def query_last_cycles(self) -> dict:
        """Letzter abgeschlossener Zyklus pro Betriebsart aus der DB.

        Liest die letzten Einträge chronologisch, erkennt Zyklen anhand
        von Moduswechseln und gibt den jeweils letzten abgeschlossenen
        Zyklus für heating, dhw, disinfection zurück.

        Returns:
            Dict mit mode -> {start, end, duration_min, energy_kwh, gas_m3}
        """
        sql = """
            SELECT ts, mode, energy_total_kwh, gas_display_m3
            FROM measurements
            ORDER BY ts DESC LIMIT 3000
        """
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()

        if len(rows) < 2:
            return {}

        # Chronologisch sortieren (älteste zuerst)
        rows = list(reversed(rows))

        from datetime import datetime

        # Zyklen sammeln: jeder zusammenhängende Block gleichen Modus
        cycles: list[dict] = []
        block_start = 0
        for i in range(1, len(rows)):
            if rows[i]["mode"] != rows[block_start]["mode"]:
                mode = rows[block_start]["mode"]
                if mode in ("heating", "dhw", "disinfection"):
                    # Dauer: vom Block-Start bis zum nächsten Eintrag nach dem Block
                    t_start = datetime.fromisoformat(rows[block_start]["ts"])
                    t_end = datetime.fromisoformat(rows[i]["ts"])
                    dur = (t_end - t_start).total_seconds()

                    # Energie/Gas: Differenz zwischen nächstem Eintrag und Block-Start
                    # (nächster Eintrag = rows[i] hat den kumulierten Wert am Ende)
                    e_start = rows[block_start]["energy_total_kwh"] or 0
                    e_end = rows[i]["energy_total_kwh"] or 0
                    g_start = rows[block_start]["gas_display_m3"] or 0
                    g_end = rows[i]["gas_display_m3"] or 0

                    cycles.append({
                        "mode": mode,
                        "start": rows[block_start]["ts"],
                        "end": rows[i]["ts"],
                        "duration_min": round(dur / 60, 1),
                        "energy_kwh": round(e_end - e_start, 2),
                        "gas_m3": round(g_end - g_start, 3),
                    })
                block_start = i

        # Letzten Zyklus pro Modus (rückwärts durch cycles)
        result: dict = {}
        for c in reversed(cycles):
            if c["mode"] not in result:
                result[c["mode"]] = c
            if len(result) >= 3:
                break

        return result

    def cleanup(self, keep_years: int = 2) -> int:
        """Erstellt Backup und löscht Daten älter als keep_years Jahre.

        Backup: heating.db.bak (wird bei jedem Start überschrieben)

        Returns:
            Anzahl gelöschter Zeilen.
        """
        import shutil

        # Backup erstellen (eine Datei, wird überschrieben)
        if self.db_path.exists():
            backup_path = self.db_path.with_suffix(".db.bak")
            shutil.copy2(self.db_path, backup_path)
            logger.info("DB Backup: %s", backup_path.name)

        # Alte Daten löschen
        sql = "DELETE FROM measurements WHERE ts < datetime('now', ?)"
        with self._conn() as conn:
            cursor = conn.execute(sql, (f"-{keep_years} years",))
            deleted = cursor.rowcount
            if deleted > 0:
                conn.execute("VACUUM")
            conn.commit()
        if deleted > 0:
            logger.info(
                "DB Cleanup: %d Zeilen älter als %d Jahre gelöscht",
                deleted,
                keep_years,
            )
        return deleted
