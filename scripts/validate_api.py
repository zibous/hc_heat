#!/usr/bin/env python3
"""Validiert EMS-ESP API-Daten gegen die internen Models.

Prüft:
1. Welche API-Felder werden gemappt (und auf welchen Wert)
2. Welche API-Felder werden NICHT gemappt (verwaist)
3. Welche Model-Felder bleiben None (kein Mapping greift)

Aufruf: python3 scripts/validate_api.py
"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.app_config import load_config
from lib.models.boiler import Boiler
from lib.models.system_data import SystemData
from lib.models.heating_circuit import HeatingCircuit
from lib.models.thermostat import Thermostat
from lib.models.gas_meter import GasMeter

config = load_config()


def fetch(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ❌ {url}: {e}")
        return None


def check_model(name, obj, raw_keys, section_label):
    """Vergleicht Model-Felder mit API-Keys."""
    from dataclasses import fields

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    model_fields = {
        f.name: getattr(obj, f.name) for f in fields(obj) if f.name != "raw"
    }

    filled = {k: v for k, v in model_fields.items() if v is not None}
    empty = {k: v for k, v in model_fields.items() if v is None}

    print(f"\n  ✅ Gemappt ({len(filled)}/{len(model_fields)}):")
    for k, v in sorted(filled.items()):
        val = repr(v) if not isinstance(v, (int, float, bool)) else str(v)
        if len(val) > 60:
            val = val[:57] + "..."
        print(f"     {k:30s} = {val}")

    if empty:
        print(f"\n  ⚠️  None ({len(empty)}):")
        for k in sorted(empty.keys()):
            print(f"     {k}")

    # Ungenutzte API-Keys
    from lib.utils.field_mapper import load_mappings

    mappings = load_mappings()
    section_map = mappings.get(section_label, {})
    all_mapped_api_keys = set()
    for field_name, api_keys in section_map.items():
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        all_mapped_api_keys.update(api_keys)

    unmapped = set(raw_keys) - all_mapped_api_keys
    # Filter out nested dicts
    unmapped = {
        k
        for k in unmapped
        if not isinstance(k, str) or k not in ("dhw", "hc1", "hc2", "hc3", "hc4")
    }
    if unmapped:
        print(f"\n  📋 API-Felder ohne Mapping ({len(unmapped)}):")
        for k in sorted(unmapped):
            print(f"     {k}")

    return len(filled), len(model_fields)


print("=" * 60)
print("  EMS-ESP API Validierung gegen interne Models")
print("=" * 60)

# ── Boiler API ──
boiler_url = config.heating.sensor_url
print(f"\n📡 Boiler API: {boiler_url}")
boiler_raw = fetch(boiler_url)
if boiler_raw:
    dhw_raw = boiler_raw.get("dhw", {})
    top_keys = [k for k in boiler_raw.keys() if k != "dhw"]

    boiler = Boiler.from_api(boiler_raw)
    check_model("Boiler", boiler, top_keys, "boiler")

    if boiler.dhw:
        check_model("DHW (Warmwasser)", boiler.dhw, list(dhw_raw.keys()), "dhw")

    if boiler.disinfection:
        check_model("Disinfection", boiler.disinfection, list(dhw_raw.keys()), "dhw")

    system = SystemData.from_api(boiler_raw)
    check_model("SystemData", system, top_keys, "system")

    hc = HeatingCircuit.from_api(boiler_raw)
    check_model("HeatingCircuit", hc, top_keys, "heating_circuit")

# ── Thermostat API ──
therm_url = config.heating.thermostat_url
print(f"\n📡 Thermostat API: {therm_url}")
therm_raw = fetch(therm_url)
if therm_raw:
    thermostat = Thermostat.from_api(therm_raw)
    therm_top = [
        k for k in therm_raw.keys() if k not in ("hc1", "hc2", "hc3", "hc4", "dhw")
    ]
    check_model("Thermostat (Top-Level)", thermostat, therm_top, "thermostat")

    hc1_raw = therm_raw.get("hc1", {})
    if thermostat.hc1:
        check_model(
            "ThermostatHC1", thermostat.hc1, list(hc1_raw.keys()), "thermostat_hc1"
        )

    dhw_raw_th = therm_raw.get("dhw", {})
    if thermostat.wwk:
        check_model(
            "ThermostatWWK", thermostat.wwk, list(dhw_raw_th.keys()), "thermostat_wwk"
        )

# ── Gaszähler ──
gas_url = config.gasmeter.sensor_url
if gas_url:
    print(f"\n📡 Gaszähler: {gas_url}")
    gas_raw = fetch(gas_url)
    if gas_raw:
        cfg = {
            "idx_display": config.gasmeter.idx_display,
            "idx_total": config.gasmeter.idx_total,
            "idx_ts": config.gasmeter.idx_ts,
        }
        gas = GasMeter.from_api(gas_raw, cfg)
        print("\n  ✅ GasMeter:")
        print(f"     display_m3  = {gas.display_m3}")
        print(f"     total_m3    = {gas.total_m3}")
        print(f"     timestamp   = {gas.timestamp}")

# ── Zusammenfassung ──
print(f"\n{'='*60}")
print("  Validierung abgeschlossen")
print(f"{'='*60}")
