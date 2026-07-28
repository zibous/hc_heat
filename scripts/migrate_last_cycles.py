#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einmalige Migration: Befüllt die last_cycles-Tabelle aus den bestehenden Daten.

Sucht den letzten abgeschlossenen Zyklus pro Modus (heating, dhw, disinfection)
aus der measurements-Tabelle und schreibt ihn in last_cycles.

Usage:
    python scripts/migrate_last_cycles.py
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "heating.db"


def find_last_cycle(conn: sqlite3.Connection, target_mode: str) -> dict | None:
    """Findet den letzten substantiellen Zyklus (>= 2 min) für einen Modus."""

    # Strategie: Letzte 50 Moduswechsel scannen (nicht die ganze DB)
    # Hole die letzten Einträge rückwärts bis wir den Modus finden
    sql = """
        SELECT ts, mode, energy_total_kwh, gas_display_m3
        FROM measurements
        WHERE ts >= (
            SELECT ts FROM measurements WHERE mode = ?
            ORDER BY ts DESC LIMIT 1 OFFSET 200
        )
        ORDER BY ts ASC
    """
    rows = conn.execute(sql, (target_mode,)).fetchall()

    if not rows:
        # Fallback: ganzer Bereich des Modus
        rows = conn.execute(
            "SELECT ts, mode, energy_total_kwh, gas_display_m3 FROM measurements ORDER BY ts DESC LIMIT 5000"
        ).fetchall()
        rows = list(reversed(rows))

    if len(rows) < 2:
        return None

    # Zyklen erkennen
    cycles = []
    block_start = 0
    for i in range(1, len(rows)):
        if rows[i]["mode"] != rows[block_start]["mode"]:
            mode = rows[block_start]["mode"]
            if mode == target_mode:
                t_start = datetime.fromisoformat(rows[block_start]["ts"])
                t_end = datetime.fromisoformat(rows[i]["ts"])
                dur = (t_end - t_start).total_seconds()

                if dur >= 120:  # Mindestens 2 Minuten
                    e_start = rows[block_start]["energy_total_kwh"] or 0
                    e_end = rows[i]["energy_total_kwh"] or rows[i - 1]["energy_total_kwh"] or e_start

                    g_start = None
                    g_end = None
                    for j in range(block_start, min(i + 1, len(rows))):
                        val = rows[j]["gas_display_m3"]
                        if val is not None:
                            if g_start is None:
                                g_start = val
                            g_end = val

                    gas_diff = round(g_end - g_start, 3) if (g_start is not None and g_end is not None) else None

                    cycles.append({
                        "mode": target_mode,
                        "start_ts": rows[block_start]["ts"],
                        "end_ts": rows[i]["ts"],
                        "duration_min": round(dur / 60, 1),
                        "energy_kwh": round(e_end - e_start, 2),
                        "gas_m3": gas_diff,
                    })
            block_start = i

    # Letzten (neuesten) Zyklus zurückgeben
    return cycles[-1] if cycles else None


def main():
    if not DB_PATH.exists():
        print(f"DB nicht gefunden: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Tabelle anlegen falls noch nicht vorhanden
    conn.execute("""
        CREATE TABLE IF NOT EXISTS last_cycles (
            mode TEXT PRIMARY KEY,
            start_ts TEXT,
            end_ts TEXT,
            duration_min REAL,
            energy_kwh REAL,
            gas_m3 REAL
        )
    """)
    conn.commit()

    for mode in ("heating", "dhw", "disinfection"):
        cycle = find_last_cycle(conn, mode)
        if cycle:
            conn.execute("""
                INSERT INTO last_cycles (mode, start_ts, end_ts, duration_min, energy_kwh, gas_m3)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mode) DO UPDATE SET
                    start_ts = excluded.start_ts,
                    end_ts = excluded.end_ts,
                    duration_min = excluded.duration_min,
                    energy_kwh = excluded.energy_kwh,
                    gas_m3 = excluded.gas_m3
            """, (cycle["mode"], cycle["start_ts"], cycle["end_ts"],
                  cycle["duration_min"], cycle["energy_kwh"], cycle["gas_m3"]))
            print(f"✅ {mode:14s} | {cycle['start_ts'][:10]} | {cycle['duration_min']:6.1f} min | {cycle['gas_m3'] or 0:.3f} m³ | {cycle['energy_kwh']:.2f} kWh")
        else:
            print(f"❌ {mode:14s} | kein Zyklus gefunden")

    conn.commit()
    conn.close()
    print("\nMigration abgeschlossen.")


if __name__ == "__main__":
    main()
