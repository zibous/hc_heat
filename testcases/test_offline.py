#!/usr/bin/env python3
"""Offline-Test: Prüft alle Models gegen die echten Raw-JSON-Dateien.

Ausführen auf dem Server:
  python3 test_offline.py

Kein Netzwerk nötig – nutzt nur data/raw/*.json
"""

import json
import sys
from pathlib import Path

# Farben für Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0
warnings = 0


def ok(msg: str) -> None:
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"  {YELLOW}⚠{RESET} {msg}")


def check(condition: bool, msg_ok: str, msg_fail: str) -> None:
    if condition:
        ok(msg_ok)
    else:
        fail(msg_fail)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ============================================================
print(f"\n{BOLD}===  hc_heat Offline-Test ==={RESET}\n")

# ============================================================
# 1. Imports prüfen
# ============================================================
print(f"{BOLD}1. Imports{RESET}")
try:
    from lib.utils.helpers import safe_get, to_float, to_bool, to_int, parse_timestamp

    ok("helpers importiert")
except Exception as e:
    fail(f"helpers Import: {e}")
    sys.exit(1)

try:
    from lib.models.boiler import Boiler
    from lib.models.dhw import DHW
    from lib.models.disinfection import Disinfection
    from lib.models.system_data import SystemData
    from lib.models.heating_circuit import HeatingCircuit
    from lib.models.gas_meter import GasMeter
    from lib.models.heating_snapshot import HeatingSnapshot
    from lib.models.heating_system import HeatingSystem
    from lib.models.operation_state import OperationMode, OperationState

    ok("alle Models importiert")
except Exception as e:
    fail(f"Models Import: {e}")
    sys.exit(1)

try:
    from lib.calc.consumption_calc import ConsumptionCalculator
    from lib.calc.cost_calc import CostCalculator
    from lib.calc.runtime_calc import RuntimeCalculator
    from lib.calc.error_log import ErrorLog

    ok("alle Calc-Module importiert")
except Exception as e:
    fail(f"Calc Import: {e}")
    sys.exit(1)

try:
    from config.app_config import load_config, load_costs, AppConfig

    ok("Config importiert")
except Exception as e:
    fail(f"Config Import: {e}")
    sys.exit(1)

# ============================================================
# 2. Helpers testen
# ============================================================
print(f"\n{BOLD}2. Helpers{RESET}")

check(safe_get({"a": 1, "b": 2}, "a") == 1, "safe_get('a') = 1", "safe_get('a') falsch")
check(
    safe_get({"a": 1}, "x", "a") == 1,
    "safe_get('x','a') Fallback = 1",
    "safe_get Fallback falsch",
)
check(
    safe_get({"a": None}, "a", default=99) == 99,
    "safe_get None -> default",
    "safe_get None falsch",
)
check(
    safe_get({}, "x", default=42) == 42,
    "safe_get leer -> default",
    "safe_get leer falsch",
)

check(to_float("3.14") == 3.14, "to_float('3.14')", "to_float falsch")
check(to_float(None) is None, "to_float(None) = None", "to_float None falsch")
check(to_float("abc") is None, "to_float('abc') = None", "to_float abc falsch")

check(to_int("42") == 42, "to_int('42')", "to_int falsch")
check(to_int(None) is None, "to_int(None) = None", "to_int None falsch")

check(to_bool("an") is True, "to_bool('an') = True", "to_bool 'an' falsch")
check(to_bool("aus") is False, "to_bool('aus') = False", "to_bool 'aus' falsch")
check(to_bool(True) is True, "to_bool(True) = True", "to_bool True falsch")
check(to_bool(None) is None, "to_bool(None) = None", "to_bool None falsch")

ts = parse_timestamp("2026-04-28T16:10:44")
check(
    ts == "2026-04-28T16:10:44",
    f"parse_timestamp ISO = {ts}",
    f"parse_timestamp ISO falsch: {ts}",
)

ts2 = parse_timestamp("2026-04-28T16:10:44 CEST")
check(
    ts2 == "2026-04-28T16:10:44",
    f"parse_timestamp CEST = {ts2}",
    f"parse_timestamp CEST falsch: {ts2}",
)

# ============================================================
# 3. Boiler Model gegen api-boiler.json
# ============================================================
print(f"\n{BOLD}3. Boiler Model (api-boiler.json){RESET}")

boiler_raw = load_json("data/raw/api-boiler.json")
boiler = Boiler.from_api(boiler_raw)

check(
    boiler.flow_temp == 25.8,
    f"flow_temp = {boiler.flow_temp}",
    f"flow_temp falsch: {boiler.flow_temp}",
)
check(
    boiler.flow_set_temp == 28,
    f"flow_set_temp = {boiler.flow_set_temp}",
    f"flow_set_temp falsch: {boiler.flow_set_temp}",
)
check(
    boiler.outdoor_temp == 22.1,
    f"outdoor_temp = {boiler.outdoor_temp}",
    f"outdoor_temp falsch: {boiler.outdoor_temp}",
)
check(
    boiler.burner_active is False,
    f"burner_active = {boiler.burner_active}",
    f"burner_active falsch: {boiler.burner_active}",
)
check(
    boiler.heating_active is False,
    f"heating_active = {boiler.heating_active}",
    f"heating_active falsch: {boiler.heating_active}",
)
check(
    boiler.heating_enabled is True,
    f"heating_enabled = {boiler.heating_enabled}",
    f"heating_enabled falsch: {boiler.heating_enabled}",
)
check(
    boiler.tapwater_active is False,
    f"tapwater_active = {boiler.tapwater_active}",
    f"tapwater_active falsch: {boiler.tapwater_active}",
)
check(
    boiler.burner_power_percent == 0,
    f"burner_power_percent = {boiler.burner_power_percent}",
    f"burner_power_percent falsch: {boiler.burner_power_percent}",
)
check(
    boiler.nominal_power_kw == 14,
    f"nominal_power_kw = {boiler.nominal_power_kw}",
    f"nominal_power_kw falsch: {boiler.nominal_power_kw}",
)
check(
    boiler.pump_active is True,
    f"pump_active = {boiler.pump_active}",
    f"pump_active falsch: {boiler.pump_active}",
)
check(
    boiler.pump_modulation == 41,
    f"pump_modulation = {boiler.pump_modulation}",
    f"pump_modulation falsch: {boiler.pump_modulation}",
)
check(
    boiler.pump_mode == "deltaP-2",
    f"pump_mode = {boiler.pump_mode}",
    f"pump_mode falsch: {boiler.pump_mode}",
)
check(
    boiler.energy_total_kwh == 15870.88,
    f"energy_total = {boiler.energy_total_kwh}",
    f"energy_total falsch: {boiler.energy_total_kwh}",
)
check(
    boiler.energy_heat_kwh == 11147.47,
    f"energy_heat = {boiler.energy_heat_kwh}",
    f"energy_heat falsch: {boiler.energy_heat_kwh}",
)
check(
    boiler.energy_dhw_kwh == 4723.42,
    f"energy_dhw = {boiler.energy_dhw_kwh}",
    f"energy_dhw falsch: {boiler.energy_dhw_kwh}",
)
check(
    boiler.burner_starts == 60531,
    f"burner_starts = {boiler.burner_starts}",
    f"burner_starts falsch: {boiler.burner_starts}",
)
check(
    boiler.burner_runtime_min == 482354,
    f"burner_runtime = {boiler.burner_runtime_min}",
    f"burner_runtime falsch: {boiler.burner_runtime_min}",
)
check(
    boiler.heating_runtime_min == 433376,
    f"heating_runtime = {boiler.heating_runtime_min}",
    f"heating_runtime falsch: {boiler.heating_runtime_min}",
)
check(
    boiler.heating_starts == 55073,
    f"heating_starts = {boiler.heating_starts}",
    f"heating_starts falsch: {boiler.heating_starts}",
)
check(boiler.lastcode is not None, f"lastcode = {boiler.lastcode}", "lastcode ist None")
check(
    boiler.service_code == "0Y",
    f"service_code = {boiler.service_code}",
    f"service_code falsch: {boiler.service_code}",
)
check(
    boiler.maintenance_date == "30.06.2026",
    f"maintenance_date = {boiler.maintenance_date}",
    f"maintenance_date falsch: {boiler.maintenance_date}",
)

# Brennerleistung
power = boiler.current_power_kw()
check(power == 0.0, f"current_power_kw = {power}", f"current_power_kw falsch: {power}")

# ============================================================
# 4. DHW Model
# ============================================================
print(f"\n{BOLD}4. DHW Model{RESET}")

dhw = boiler.dhw
check(dhw is not None, "DHW Objekt vorhanden", "DHW ist None!")
if dhw:
    check(
        dhw.curtemp == 58.6,
        f"dhw.curtemp = {dhw.curtemp}",
        f"dhw.curtemp falsch: {dhw.curtemp}",
    )
    check(
        dhw.settemp == 57,
        f"dhw.settemp = {dhw.settemp}",
        f"dhw.settemp falsch: {dhw.settemp}",
    )
    check(
        dhw.seltemp == 57,
        f"dhw.seltemp = {dhw.seltemp}",
        f"dhw.seltemp falsch: {dhw.seltemp}",
    )
    check(
        dhw.flowtempoffset == 40,
        f"dhw.flowtempoffset = {dhw.flowtempoffset}",
        f"dhw.flowtempoffset falsch: {dhw.flowtempoffset}",
    )
    check(
        dhw.comfort == "Eco",
        f"dhw.comfort = {dhw.comfort}",
        f"dhw.comfort falsch: {dhw.comfort}",
    )
    check(
        dhw.storage_type == "Speicher",
        f"dhw.type = {dhw.storage_type}",
        f"dhw.type falsch: {dhw.storage_type}",
    )
    check(
        dhw.activated is True,
        f"dhw.activated = {dhw.activated}",
        f"dhw.activated falsch: {dhw.activated}",
    )
    check(
        dhw.active is False,
        f"dhw.active = {dhw.active}",
        f"dhw.active falsch: {dhw.active}",
    )
    check(
        dhw.charging is False,
        f"dhw.charging = {dhw.charging}",
        f"dhw.charging falsch: {dhw.charging}",
    )
    check(
        dhw.disinfecting is False,
        f"dhw.disinfecting = {dhw.disinfecting}",
        f"dhw.disinfecting falsch: {dhw.disinfecting}",
    )
    check(
        dhw.disinfection_temp == 70,
        f"dhw.disinfection_temp = {dhw.disinfection_temp}",
        f"dhw.disinfection_temp falsch: {dhw.disinfection_temp}",
    )
    check(
        dhw.tempok is True,
        f"dhw.tempok = {dhw.tempok}",
        f"dhw.tempok falsch: {dhw.tempok}",
    )
    check(
        dhw.starts == 5458,
        f"dhw.starts = {dhw.starts}",
        f"dhw.starts falsch: {dhw.starts}",
    )
    check(
        dhw.workm == 48978, f"dhw.workm = {dhw.workm}", f"dhw.workm falsch: {dhw.workm}"
    )
    check(dhw.nrg == 4723.42, f"dhw.nrg = {dhw.nrg}", f"dhw.nrg falsch: {dhw.nrg}")

# ============================================================
# 5. Disinfection Model
# ============================================================
print(f"\n{BOLD}5. Disinfection Model{RESET}")

dis = boiler.disinfection
check(dis is not None, "Disinfection Objekt vorhanden", "Disinfection ist None!")
if dis:
    check(
        dis.active is False,
        f"dis.active = {dis.active}",
        f"dis.active falsch: {dis.active}",
    )
    check(
        dis.disinfection_temp == 70,
        f"dis.temp = {dis.disinfection_temp}",
        f"dis.temp falsch: {dis.disinfection_temp}",
    )
    check(
        dis.curtemp == 58.6,
        f"dis.curtemp = {dis.curtemp}",
        f"dis.curtemp falsch: {dis.curtemp}",
    )

# ============================================================
# 6. SystemData Model
# ============================================================
print(f"\n{BOLD}6. SystemData Model (api-boiler.json){RESET}")

system = SystemData.from_api(boiler_raw)
check(
    system.outdoor_temp == 22.1,
    f"outdoor_temp = {system.outdoor_temp}",
    f"outdoor_temp falsch: {system.outdoor_temp}",
)
check(
    system.heating_off is False,
    f"heating_off = {system.heating_off}",
    f"heating_off falsch: {system.heating_off}",
)
check(
    system.heating_active is False,
    f"heating_active = {system.heating_active}",
    f"heating_active falsch: {system.heating_active}",
)
check(
    system.tapwater_active is False,
    f"tapwater_active = {system.tapwater_active}",
    f"tapwater_active falsch: {system.tapwater_active}",
)
check(
    system.curve_on is False,
    f"curve_on = {system.curve_on}",
    f"curve_on falsch: {system.curve_on}",
)
check(
    system.summer_temp == 16,
    f"summer_temp = {system.summer_temp}",
    f"summer_temp falsch: {system.summer_temp}",
)
check(
    system.frost_temp == 5,
    f"frost_temp = {system.frost_temp}",
    f"frost_temp falsch: {system.frost_temp}",
)

# ============================================================
# 7. HeatingCircuit Model
# ============================================================
print(f"\n{BOLD}7. HeatingCircuit Model (api-boiler.json){RESET}")

hc = HeatingCircuit.from_api(boiler_raw)
check(
    hc.flow_temp == 25.8,
    f"flow_temp = {hc.flow_temp}",
    f"flow_temp falsch: {hc.flow_temp}",
)
check(
    hc.set_flow_temp == 28,
    f"set_flow_temp = {hc.set_flow_temp}",
    f"set_flow_temp falsch: {hc.set_flow_temp}",
)
check(
    hc.return_temp is None,
    "return_temp = None (nicht im Boiler-EP)",
    f"return_temp unerwartet: {hc.return_temp}",
)
check(
    hc.pump_active is True,
    f"pump_active = {hc.pump_active}",
    f"pump_active falsch: {hc.pump_active}",
)
check(hc.mode == "deltaP-2", f"mode = {hc.mode}", f"mode falsch: {hc.mode}")

# ============================================================
# 8. GasMeter Model
# ============================================================
print(f"\n{BOLD}8. GasMeter Model (gasmeter.json){RESET}")

gas_raw = load_json("data/raw/gasmeter.json")
gas = GasMeter.from_api(gas_raw)
check(
    gas.total_m3 == 32380.797,
    f"total_m3 = {gas.total_m3}",
    f"total_m3 falsch: {gas.total_m3}",
)
check(
    gas.partial_m3 == 3320.143,
    f"partial_m3 = {gas.partial_m3}",
    f"partial_m3 falsch: {gas.partial_m3}",
)
check(gas.timestamp is not None, f"timestamp = {gas.timestamp}", "timestamp ist None")

# ============================================================
# 9. Calc-Module
# ============================================================
print(f"\n{BOLD}9. Berechnungsmodule{RESET}")

# ConsumptionCalculator
cc = ConsumptionCalculator()
result = cc.calculate(boiler)
check(
    result.energy_total_kwh == 15870.88,
    f"consumption.total = {result.energy_total_kwh}",
    f"consumption.total falsch: {result.energy_total_kwh}",
)
check(
    result.energy_heat_kwh == 11147.47,
    f"consumption.heat = {result.energy_heat_kwh}",
    f"consumption.heat falsch: {result.energy_heat_kwh}",
)
check(
    result.energy_dhw_kwh == 4723.42,
    f"consumption.dhw = {result.energy_dhw_kwh}",
    f"consumption.dhw falsch: {result.energy_dhw_kwh}",
)
check(
    result.dhw_runtime_calculated_min == 482354 - 433376,
    f"dhw_runtime_calc = {result.dhw_runtime_calculated_min}",
    f"dhw_runtime_calc falsch",
)
check(
    result.dhw_starts_calculated == 60531 - 55073,
    f"dhw_starts_calc = {result.dhw_starts_calculated}",
    f"dhw_starts_calc falsch",
)

# CostCalculator
from config.app_config import CostSettings

costs = CostSettings(
    gas_price_per_m3=1.05,
    gas_price_per_kwh=0.103,
    energy_price_per_kwh=0.35,
    gas_kwh_per_m3=10.19,
)
cost_calc = CostCalculator(costs)
cost_result = cost_calc.calculate(15870.88, 11147.47, 4723.42)
check(
    cost_result.gas_total_eur > 0,
    f"gas_total_eur = {cost_result.gas_total_eur:.2f}",
    "gas_total_eur = 0",
)
check(
    cost_result.gas_heat_eur > 0,
    f"gas_heat_eur = {cost_result.gas_heat_eur:.2f}",
    "gas_heat_eur = 0",
)

# RuntimeCalculator
rt = RuntimeCalculator()
mode = rt.determine_mode(boiler)
check(
    mode == OperationMode.STANDBY,
    f"mode = {mode.value} (Brenner aus)",
    f"mode falsch: {mode.value}",
)

state = rt.update(boiler)
check(
    state.mode == OperationMode.STANDBY,
    f"state.mode = {state.mode.value}",
    f"state.mode falsch: {state.mode.value}",
)

# ErrorLog
el = ErrorLog()
err = el.check_error(boiler.lastcode)
check(
    err is not None,
    f"Erster Fehler erkannt: {err.code[:30]}...",
    "Fehler nicht erkannt",
)
err2 = el.check_error(boiler.lastcode)
check(err2 is None, "Duplikat-Fehler ignoriert", "Duplikat nicht ignoriert")
check(el.count == 1, f"error_count = {el.count}", f"error_count falsch: {el.count}")

# ============================================================
# 10. Config
# ============================================================
print(f"\n{BOLD}10. Config{RESET}")

costs_loaded = load_costs()
check(
    costs_loaded.gas_price_per_m3 > 0,
    f"gas_price = {costs_loaded.gas_price_per_m3}",
    "gas_price = 0 (costs.yaml fehlt?)",
)
check(
    costs_loaded.gas_kwh_per_m3 == 10.19,
    f"gas_kwh_per_m3 = {costs_loaded.gas_kwh_per_m3}",
    f"gas_kwh_per_m3 falsch: {costs_loaded.gas_kwh_per_m3}",
)

# ============================================================
# 11. Snapshot Serialisierung
# ============================================================
print(f"\n{BOLD}11. Snapshot Serialisierung{RESET}")

from datetime import datetime
from lib.core.history_manager import HistoryManager
import tempfile, shutil

snapshot = HeatingSnapshot(
    timestamp=datetime.now(),
    system=system,
    boiler=boiler,
    heating=hc,
    gas=gas,
)

# In temp-Verzeichnis speichern
tmp_dir = tempfile.mkdtemp()
try:
    hm = HistoryManager(folder=tmp_dir)
    path = hm.save_snapshot(snapshot)
    check(
        path.exists(),
        f"Snapshot gespeichert: {path.name}",
        "Snapshot nicht gespeichert",
    )

    loaded = hm.load_snapshot(path)
    check(loaded is not None, "Snapshot geladen", "Snapshot laden fehlgeschlagen")
    if loaded:
        check(
            loaded["boiler"]["flow_temp"] == 25.8,
            "Serialisierung flow_temp korrekt",
            "Serialisierung flow_temp falsch",
        )
        check(
            loaded["boiler"]["dhw"]["curtemp"] == 58.6,
            "Serialisierung dhw.curtemp korrekt",
            "Serialisierung dhw.curtemp falsch",
        )
        check(
            loaded["gas"]["total_m3"] == 32380.797,
            "Serialisierung gas.total_m3 korrekt",
            "Serialisierung gas.total_m3 falsch",
        )
        check(
            loaded["system"]["outdoor_temp"] == 22.1,
            "Serialisierung system.outdoor_temp korrekt",
            "Serialisierung system.outdoor_temp falsch",
        )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# ============================================================
# Zusammenfassung
# ============================================================
print(f"\n{BOLD}{'='*50}{RESET}")
total = passed + failed
print(f"{BOLD}Ergebnis: {passed}/{total} Tests bestanden{RESET}")
if warnings:
    print(f"{YELLOW}Warnungen: {warnings}{RESET}")
if failed:
    print(f"{RED}FEHLGESCHLAGEN: {failed} Tests{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}ALLE TESTS BESTANDEN ✓{RESET}")
    sys.exit(0)
