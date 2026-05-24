#!/usr/bin/env python3
"""Exportiert History-CSV-Dateien aus der SQLite-Datenbank.

Erzeugt wöchentliche CSV-Dateien im gleichen Format wie der
HistoryWriter, damit man DB-Daten mit Live-Daten vergleichen kann.

Verwendung:
    python3 scripts/export_history.py              # Alle Daten
    python3 scripts/export_history.py --days 7     # Letzte 7 Tage
    python3 scripts/export_history.py --from 2026-05-01 --to 2026-05-04
    python3 scripts/export_history.py --out ./data/history   # In History-Ordner

Ausgabe: data/history/2026-W18.csv, 2026-W19.csv, ...
"""

import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.utils.env_loader import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from lib.core.db_manager import DBManager, DB_PATH

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


def week_key(ts_str: str) -> str:
    """YYYY-WNN aus ISO-Timestamp."""
    dt = datetime.fromisoformat(ts_str)
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def export(db_path: Path, out_dir: Path, start: str = "", end: str = ""):
    db = DBManager(db_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Daten laden
    if start and end:
        rows = db.query_range(start, end)
    else:
        rows = db.query_all()

    if not rows:
        print("Keine Daten gefunden.")
        return

    print(f"Gefunden: {len(rows)} Einträge")
    print(f"Zeitraum: {rows[0]['ts'][:10]} bis {rows[-1]['ts'][:10]}")

    # Nach Wochen gruppieren
    weeks: dict[str, list] = defaultdict(list)
    for row in rows:
        ts = row.get("ts", "")
        if not ts:
            continue
        wk = week_key(ts)
        weeks[wk].append(row)

    # Pro Woche eine CSV schreiben
    total_written = 0
    for wk in sorted(weeks.keys()):
        filename = f"{wk}.csv"
        filepath = out_dir / filename
        wk_rows = weeks[wk]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(COLUMNS)
            for row in wk_rows:
                writer.writerow([row.get(col, "") for col in COLUMNS])

        total_written += len(wk_rows)
        # Statistik pro Woche
        modes = defaultdict(int)
        for r in wk_rows:
            modes[r.get("mode", "?")] += 1
        mode_str = " · ".join(f"{m}={c}" for m, c in sorted(modes.items()))
        print(f"  {filename}: {len(wk_rows)} Einträge ({mode_str})")

    print(f"\n✅ {len(weeks)} Dateien geschrieben → {out_dir}/")
    print(f"   {total_written} Einträge gesamt")

    # Grenzfälle anzeigen
    print("\n── Grenzfälle ──")
    _show_edge_cases(rows)


def _show_edge_cases(rows: list[dict]):
    """Zeigt interessante Grenzfälle in den Daten."""

    # 1. Moduswechsel
    transitions = []
    for i in range(1, len(rows)):
        if rows[i].get("mode") != rows[i - 1].get("mode"):
            transitions.append({
                "ts": rows[i]["ts"],
                "from": rows[i - 1]["mode"],
                "to": rows[i]["mode"],
            })

    print(f"\n  Moduswechsel: {len(transitions)}")
    mode_counts = defaultdict(int)
    for t in transitions:
        key = f"{t['from']} → {t['to']}"
        mode_counts[key] += 1
    for key, count in sorted(mode_counts.items(), key=lambda x: -x[1]):
        print(f"    {key}: {count}x")

    # 2. Kürzeste und längste Zyklen pro Modus
    print("\n  Zyklen (Dauer):")
    cycles = []
    start_idx = 0
    for i in range(1, len(rows)):
        if rows[i].get("mode") != rows[start_idx].get("mode"):
            mode = rows[start_idx]["mode"]
            ts_start = rows[start_idx]["ts"]
            ts_end = rows[i]["ts"]
            try:
                dur = (datetime.fromisoformat(ts_end) - datetime.fromisoformat(ts_start)).total_seconds()
                cycles.append({"mode": mode, "start": ts_start, "dur_s": dur})
            except Exception:
                pass
            start_idx = i

    for mode in ["heating", "dhw", "disinfection", "standby"]:
        mc = [c for c in cycles if c["mode"] == mode]
        if not mc:
            continue
        shortest = min(mc, key=lambda c: c["dur_s"])
        longest = max(mc, key=lambda c: c["dur_s"])
        avg = sum(c["dur_s"] for c in mc) / len(mc)
        print(f"    {mode}: {len(mc)} Zyklen")
        print(f"      kürzester: {shortest['dur_s']:.0f}s ({shortest['start'][:16]})")
        print(f"      längster:  {longest['dur_s']:.0f}s ({longest['start'][:16]})")
        print(f"      ⌀ {avg:.0f}s ({avg/60:.1f} min)")

    # 3. Einzelne Einträge (1-Punkt-Zyklen)
    single_entries = [c for c in cycles if c["mode"] != "standby" and c["dur_s"] < 120]
    if single_entries:
        print(f"\n  ⚠️  Kurze Zyklen (<2 min): {len(single_entries)}")
        for c in single_entries[:5]:
            print(f"    {c['start'][:16]} {c['mode']} ({c['dur_s']:.0f}s)")

    # 4. Temperatur-Extremwerte
    print("\n  Temperatur-Extremwerte:")
    outdoor = [r["outdoor_temp"] for r in rows if r.get("outdoor_temp") is not None]
    flow = [r["flow_temp"] for r in rows if r.get("flow_temp") is not None]
    dhw = [r["dhw_temp"] for r in rows if r.get("dhw_temp") is not None]
    if outdoor:
        print(f"    Außen:     {min(outdoor):.1f} – {max(outdoor):.1f}°C")
    if flow:
        print(f"    Vorlauf:   {min(flow):.1f} – {max(flow):.1f}°C")
    if dhw:
        print(f"    WW:        {min(dhw):.1f} – {max(dhw):.1f}°C")

    # 5. Energie-Verbrauch
    e_start = next((r["energy_total_kwh"] for r in rows if r.get("energy_total_kwh")), None)
    e_end = next((r["energy_total_kwh"] for r in reversed(rows) if r.get("energy_total_kwh")), None)
    g_start = next((r["gas_display_m3"] for r in rows if r.get("gas_display_m3")), None)
    g_end = next((r["gas_display_m3"] for r in reversed(rows) if r.get("gas_display_m3")), None)
    if e_start and e_end:
        print(f"\n  Energie gesamt: {e_end - e_start:.2f} kWh")
    if g_start and g_end:
        print(f"  Gas gesamt:     {g_end - g_start:.3f} m³")


def main():
    parser = argparse.ArgumentParser(description="Exportiert History-CSV aus SQLite")
    parser.add_argument("--days", type=int, default=0, help="Letzte N Tage (0=alle)")
    parser.add_argument("--from", dest="from_date", default="", help="Start-Datum (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", default="", help="End-Datum (YYYY-MM-DD)")
    parser.add_argument("--out", default="./data/history", help="Ausgabe-Verzeichnis")
    parser.add_argument("--db", default="", help="DB-Pfad (default: data/heating.db)")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DB_PATH
    out_dir = Path(args.out)

    if not db_path.exists():
        print(f"DB nicht gefunden: {db_path}")
        sys.exit(1)

    start = args.from_date
    end = args.to_date

    if args.days > 0 and not start:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    print(f"DB: {db_path}")
    if start and end:
        print(f"Zeitraum: {start} bis {end}")
    else:
        print("Zeitraum: alle Daten")
    print(f"Ausgabe: {out_dir}/\n")

    export(db_path, out_dir, start, end)


if __name__ == "__main__":
    main()
