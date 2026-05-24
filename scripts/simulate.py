#!/usr/bin/env python3
"""Simuliert 14 Tage Heizungsdaten in die SQLite-Datenbank.

Holt zuerst die aktuellen Zählerstände von der Heizung,
dann baut es 14 Tage rückwärts auf. Die simulierten Daten
enden beim aktuellen echten Stand.

Ausführen: python3 scripts/simulate.py
"""

import sys
import math
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.utils.env_loader import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from config.app_config import load_config
from lib.core.db_manager import DBManager, DB_PATH_SIM
from lib.core.heating_system_manager import HeatingSystemManager

# 121
DAYS = 14
NOMINAL_POWER_KW = 14


def outdoor_temp(hour: float, day: int) -> float:
    base = 2.0 + day * 0.5
    daily = -4.0 * math.cos(2 * math.pi * (hour - 14) / 24)
    return round(base + daily + random.gauss(0, 0.3), 1)


def target_flow(outdoor: float) -> float:
    if outdoor >= 18:
        return 25.0
    t = 25.0 + (45.0 - 25.0) / (-10.0 - 18.0) * (outdoor - 18.0)
    return round(min(max(t, 25.0), 50.0), 1)


def fetch_current_values(config) -> dict:
    """Holt aktuelle Zählerstände von der echten Heizung."""
    print("Hole aktuelle Zählerstände von der Heizung...")
    manager = HeatingSystemManager(config)
    snapshot = manager.load_snapshot(force_gas=True)
    b = snapshot.boiler
    gas = snapshot.gas

    values = {
        "energy_total": b.energy_total_kwh or 15900.0,
        "energy_heat": b.energy_heat_kwh or 11160.0,
        "energy_dhw": b.energy_dhw_kwh or 4734.0,
        "gas_display": gas.display_m3 if gas and gas.display_m3 else 32383.0,
        "gas_total": gas.total_m3 if gas and gas.total_m3 else 3322.0,
        "burner_starts": b.burner_starts or 60650,
        "heating_starts": b.heating_starts or 55190,
        "lastcode_boiler": b.lastcode or "",
    }
    thermostat_code = ""
    if snapshot.thermostat:
        thermostat_code = snapshot.thermostat.lastcode or ""

    values["lastcode_thermostat"] = thermostat_code

    print(f"  Energie:  {values['energy_total']:.1f} kWh")
    print(f"  Gas:      {values['gas_display']:.1f} m³")
    print(f"  Starts:   {values['burner_starts']}")
    return values


def simulate() -> None:
    config = load_config()
    current = fetch_current_values(config)

    db = DBManager(DB_PATH_SIM)
    db.clear()

    now = datetime.now()
    start = now - timedelta(days=DAYS)

    # Endwerte = aktuelle echte Werte
    # Startwerte = geschätzt 14 Tage zurück (ca. 30 kWh/Tag, 3 m³/Tag)
    est_daily_kwh = 30.0
    est_daily_gas = est_daily_kwh / 10.19

    e_total = current["energy_total"] - (DAYS * est_daily_kwh)
    e_heat = current["energy_heat"] - (DAYS * est_daily_kwh * 0.7)
    e_dhw = current["energy_dhw"] - (DAYS * est_daily_kwh * 0.3)
    gas_display = current["gas_display"] - (DAYS * est_daily_gas)
    gas_total = current["gas_total"] - (DAYS * est_daily_gas)
    b_starts = current["burner_starts"] - (DAYS * 18)
    h_starts = current["heating_starts"] - (DAYS * 14)
    b_runtime = 0
    h_runtime = 0

    dhw_temp = 55.0
    dhw_set = 57.0
    mode = "standby"
    cycle_remaining = 0
    last_dhw_end = start
    last_disinfection = start - timedelta(days=5)

    total_points = DAYS * 24 * 60
    print(f"Simuliere {DAYS} Tage ({total_points} Datenpunkte)...")
    print(f"  Start-Energie: {e_total:.1f} kWh, Start-Gas: {gas_display:.1f} m³")

    _batch = []
    for minute in range(total_points):
        ts = start + timedelta(minutes=minute)
        hour = ts.hour + ts.minute / 60.0
        day = (ts - start).days
        out = outdoor_temp(hour, day)
        t_flow = target_flow(out)

        # Desinfektion und DHW können JEDEN Modus unterbrechen (außer sich selbst)
        # DHW hat Vorrang vor Heizung (wie in der echten Anlage: 3-Wege-Ventil)
        if mode != "disinfection":
            if (
                ts.weekday() == 5
                and ts.hour == 2
                and ts.minute == 0
                and (ts - last_disinfection).days >= 6
            ):
                mode = "disinfection"
                cycle_remaining = random.randint(40, 55)
                last_disinfection = ts
                b_starts += 1
        if mode not in ("dhw", "disinfection"):
            if dhw_temp < (dhw_set - 4) and (ts - last_dhw_end).total_seconds() > 9000:
                mode = "dhw"
                cycle_remaining = random.randint(15, 25)
                b_starts += 1

        if cycle_remaining > 0:
            cycle_remaining -= 1
        else:
            # Zyklusende → nächsten Zustand bestimmen
            if mode == "heating":
                mode = "standby"
                cycle_remaining = random.randint(
                    max(15, int(25 + out * 1.5)),
                    max(30, int(50 + out * 2)),
                )
            elif mode == "dhw":
                mode = "standby"
                last_dhw_end = ts
                cycle_remaining = random.randint(10, 20)
            elif mode == "disinfection":
                mode = "standby"
                cycle_remaining = random.randint(20, 40)
            elif mode == "standby" and out < 16:
                night = 22 <= ts.hour or ts.hour < 6
                if night and random.random() > 0.3:
                    cycle_remaining = random.randint(30, 60)
                else:
                    mode = "heating"
                    burn_min = max(5, int(15 - out * 0.5))
                    burn_max = max(10, int(25 - out * 0.8))
                    cycle_remaining = random.randint(burn_min, burn_max)
                    b_starts += 1
                    h_starts += 1
            else:
                cycle_remaining = random.randint(20, 60)

        burner_on = mode in ("heating", "dhw", "disinfection")

        if mode == "heating":
            burner_power = random.randint(30, 55)
            flow_temp = t_flow + random.gauss(1, 0.8)
        elif mode == "dhw":
            burner_power = random.randint(60, 85)
            flow_temp = 65 + random.gauss(0, 1.5)
        elif mode == "disinfection":
            burner_power = random.randint(70, 90)
            flow_temp = 75 + random.gauss(0, 1.5)
        else:
            burner_power = 0
            flow_temp = max(out + 5, t_flow - 5 + random.gauss(0, 0.5))

        flow_temp = round(max(flow_temp, out + 3), 1)
        power_kw = (burner_power / 100) * NOMINAL_POWER_KW if burner_on else 0

        if mode == "dhw":
            dhw_temp = min(dhw_temp + 0.3, dhw_set + 1)
        elif mode == "disinfection":
            dhw_temp = min(dhw_temp + 0.2, 72.0)
        else:
            dhw_temp = max(dhw_temp - 0.012, out + 10)

        if burner_on:
            energy_min = power_kw / 60
            gas_min = energy_min / 10.19
            e_total += energy_min
            gas_display += gas_min
            gas_total += gas_min
            b_runtime += 1
            if mode == "heating":
                e_heat += energy_min
                h_runtime += 1
            else:
                e_dhw += energy_min

        _batch.append(
            {
                "ts": ts.isoformat(),
                "mode": mode,
                "outdoor_temp": out,
                "flow_temp": flow_temp,
                "flow_set_temp": t_flow,
                "target_flow_temp": t_flow,
                "dhw_temp": round(dhw_temp, 1),
                "dhw_set_temp": dhw_set,
                "burner_active": 1 if burner_on else 0,
                "burner_power": burner_power,
                "pump_active": 1 if burner_on else 0,
                "pump_modulation": random.randint(30, 50) if burner_on else 0,
                "energy_total_kwh": round(e_total, 2),
                "energy_heat_kwh": round(e_heat, 2),
                "energy_dhw_kwh": round(e_dhw, 2),
                "gas_display_m3": round(gas_display, 3),
                "gas_total_m3": round(gas_total, 3),
                "burner_starts": b_starts,
                "burner_runtime_min": b_runtime,
                "heating_starts": h_starts,
                "heating_runtime_min": h_runtime,
                "lastcode_boiler": current["lastcode_boiler"],
                "lastcode_thermostat": current["lastcode_thermostat"],
            }
        )
        if len(_batch) >= 2000:
            db.insert_many(_batch)
            _batch.clear()

        if minute % 5000 == 0 and minute > 0:
            print(f"  {minute}/{total_points} ({minute*100//total_points}%)")

    # Rest schreiben
    if _batch:
        db.insert_many(_batch)

    days_gas = gas_display - (current["gas_display"] - DAYS * est_daily_gas)
    print(f"\nFertig: {db.count()} Datenpunkte in {db.db_path}")
    print(f"  End-Energie: {e_total:.1f} kWh (Ziel: {current['energy_total']:.1f})")
    print(f"  End-Gas:     {gas_display:.1f} m³ (Ziel: {current['gas_display']:.1f})")
    print(f"  Gas/Tag:     {days_gas/DAYS:.1f} m³")
    print(f"  Brenner:     {b_runtime} min ({b_runtime/DAYS:.0f} min/Tag)")


if __name__ == "__main__":
    simulate()
