#!/usr/bin/env python3
"""Importiert eine History-CSV in die Simulate-DB.

Damit können echte historische Daten (mit allen Modi) im
Simulate-Modus fürs Dashboard verwendet werden.

Ausführen: python3 scripts/import_csv_to_simdb.py [CSV-Datei]
Standard:  data/history/2026-W18.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.utils.env_loader import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from lib.core.db_manager import DBManager, DB_PATH_SIM

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "history" / "2026-W18.csv"


def to_num(val, as_int=False):
    """Konvertiert String → float/int oder None."""
    if val is None or val == "":
        return None
    try:
        return int(float(val)) if as_int else float(val)
    except (ValueError, TypeError):
        return None


def import_csv(csv_path: Path) -> None:
    if not csv_path.exists():
        print(f"❌ CSV nicht gefunden: {csv_path}")
        sys.exit(1)

    db = DBManager(DB_PATH_SIM)
    db.clear()

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append({
                "ts": row.get("ts"),
                "mode": row.get("mode") or "standby",
                "outdoor_temp": to_num(row.get("outdoor_temp")),
                "flow_temp": to_num(row.get("flow_temp")),
                "flow_set_temp": to_num(row.get("flow_set_temp")),
                "target_flow_temp": to_num(row.get("target_flow_temp")),
                "dhw_temp": to_num(row.get("dhw_temp")),
                "dhw_set_temp": to_num(row.get("dhw_set_temp")),
                "burner_active": to_num(row.get("burner_active"), as_int=True),
                "burner_power": to_num(row.get("burner_power"), as_int=True),
                "pump_active": to_num(row.get("pump_active"), as_int=True),
                "pump_modulation": to_num(row.get("pump_modulation"), as_int=True),
                "energy_total_kwh": to_num(row.get("energy_total_kwh")),
                "energy_heat_kwh": to_num(row.get("energy_heat_kwh")),
                "energy_dhw_kwh": to_num(row.get("energy_dhw_kwh")),
                "gas_display_m3": to_num(row.get("gas_display_m3")),
            })

    db.insert_many(rows)
    print(f"✅ {len(rows)} Zeilen importiert → {DB_PATH_SIM.name}")
    print(f"   Quelle: {csv_path.name}")

    # Modi-Zusammenfassung
    modes = {}
    for r in rows:
        m = r["mode"]
        modes[m] = modes.get(m, 0) + 1
    for m, c in sorted(modes.items(), key=lambda x: -x[1]):
        print(f"   {m}: {c}")


if __name__ == "__main__":
    csv_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    import_csv(csv_file)
