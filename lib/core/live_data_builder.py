"""Live-Daten Builder: Baut das Dashboard-Dict aus Snapshot/Consumption/Costs/Errors.

Extrahiert die große _live_data.update({...}) Logik aus dem Hauptzyklus
in eine eigenständige, testbare Funktion.
"""

from ..models.heating_snapshot import HeatingSnapshot
from ..calc.consumption_calc import ConsumptionResult
from ..calc.cost_calc import CostResult
from ..calc.error_log import ErrorLog
from ..models.operation_state import OperationState
from typing import Optional


def build_live_data(
    snapshot: HeatingSnapshot,
    state: OperationState,
    consumption: ConsumptionResult,
    costs: CostResult,
    error_log: ErrorLog,
    today_data: dict,
    prev_values: dict,
    last_cycles: Optional[dict] = None,
) -> dict:
    """Baut das komplette Live-Daten-Dict für das Dashboard.

    Args:
        snapshot: Aktueller Heizungs-Snapshot
        state: Aktueller Betriebszustand
        consumption: Berechnete Verbrauchswerte
        costs: Berechnete Kosten
        error_log: Fehler-Log
        today_data: Tagesverbrauch (aus DB)
        prev_values: Vorherige Werte für Trend-Anzeige

    Returns:
        Dict mit allen Dashboard-Daten
    """
    b = snapshot.boiler
    dhw = b.dhw

    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "mode": state.mode.value,
        "mode_since": state.start.isoformat(),
        "mode_duration_sec": ((snapshot.timestamp - state.start).total_seconds()),
        "today": today_data,
        "system": {
            "outdoor_temp": snapshot.system.outdoor_temp,
            "heating_active": snapshot.system.heating_active,
            "heating_off": snapshot.system.heating_off,
            "tapwater_active": snapshot.system.tapwater_active,
            "curve_on": snapshot.system.curve_on,
            "summer_temp": snapshot.system.summer_temp,
            "frost_mode": snapshot.system.frost_mode,
        },
        "boiler": {
            "flow_temp": b.flow_temp,
            "flow_set_temp": b.flow_set_temp,
            "outdoor_temp": b.outdoor_temp,
            "burner_active": b.burner_active,
            "heating_active": b.heating_active,
            "heating_enabled": b.heating_enabled,
            "burner_power_percent": b.burner_power_percent,
            "flame_current": b.flame_current,
            "nominal_power_kw": b.nominal_power_kw,
            "current_power_kw": b.current_power_kw(),
            "pump_active": b.pump_active,
            "pump_modulation": b.pump_modulation,
            "pump_mode": b.pump_mode,
            "lastcode": b.lastcode,
            "service_code": b.service_code,
            "maintenance_date": b.maintenance_date,
        },
        "dhw": (
            {
                "curtemp": dhw.curtemp if dhw else None,
                "settemp": dhw.settemp if dhw else None,
                "active": dhw.active if dhw else None,
                "charging": dhw.charging if dhw else None,
                "tempok": dhw.tempok if dhw else None,
                "disinfecting": dhw.disinfecting if dhw else None,
                "disinfection_temp": dhw.disinfection_temp if dhw else None,
                "comfort": dhw.comfort if dhw else None,
                "storage_type": dhw.storage_type if dhw else None,
                "flowtempoffset": dhw.flowtempoffset if dhw else None,
            }
            if dhw
            else None
        ),
        "heating_circuit": {
            "flow_temp": snapshot.heating.flow_temp,
            "return_temp": snapshot.heating.return_temp,
            "set_flow_temp": snapshot.heating.set_flow_temp,
            "pump_active": snapshot.heating.pump_active,
        },
        "gas": (
            {
                "display_m3": snapshot.gas.display_m3,
                "total_m3": snapshot.gas.total_m3,
                "timestamp": snapshot.gas.timestamp,
            }
            if snapshot.gas
            else None
        ),
        "consumption": {
            "energy_total_kwh": consumption.energy_total_kwh,
            "energy_heat_kwh": consumption.energy_heat_kwh,
            "energy_dhw_kwh": consumption.energy_dhw_kwh,
            "energy_dhw_only_kwh": consumption.energy_dhw_only_kwh,
            "energy_disinfection_kwh": consumption.energy_disinfection_kwh,
            "period_energy_total_kwh": consumption.period_energy_total_kwh,
            "period_energy_heat_kwh": consumption.period_energy_heat_kwh,
            "period_energy_dhw_kwh": consumption.period_energy_dhw_kwh,
            "period_energy_dhw_only_kwh": consumption.period_energy_dhw_only_kwh,
            "period_energy_disinfection_kwh": consumption.period_energy_disinfection_kwh,
            "period_gas_m3": consumption.period_gas_m3,
            "burner_starts": consumption.burner_starts,
            "burner_runtime_min": consumption.burner_runtime_min,
            "heating_starts": consumption.heating_starts,
            "heating_runtime_min": consumption.heating_runtime_min,
            "dhw_runtime_min": consumption.dhw_runtime_min,
            "dhw_starts": consumption.dhw_starts,
            "disinfection_ratio": consumption.disinfection_ratio,
        },
        "costs": {
            "gas_total_eur": costs.gas_total_eur,
            "energy_total_eur": costs.energy_total_eur,
            "energy_heat_eur": costs.energy_heat_eur,
            "energy_dhw_eur": costs.energy_dhw_eur,
            "energy_dhw_only_eur": costs.energy_dhw_only_eur,
            "energy_disinfection_eur": costs.energy_disinfection_eur,
            "gas_period": costs.gas_period,
            "energy_period": costs.energy_period,
            "currency": costs.currency,
        },
        "errors": _build_errors(error_log),
        "thermostat": (
            {
                "lastcode": snapshot.thermostat.lastcode,
                "datetime": snapshot.thermostat.datetime,
                "damped_outdoor_temp": snapshot.thermostat.damped_outdoor_temp,
                "building": snapshot.thermostat.building,
                "hc1": (
                    {
                        "mode": snapshot.thermostat.hc1.mode,
                        "modetype": snapshot.thermostat.hc1.modetype,
                        "seltemp": snapshot.thermostat.hc1.seltemp,
                        "comforttemp": snapshot.thermostat.hc1.comforttemp,
                        "ecotemp": snapshot.thermostat.hc1.ecotemp,
                        "manualtemp": snapshot.thermostat.hc1.manualtemp,
                        "summertemp": snapshot.thermostat.hc1.summertemp,
                        "designtemp": snapshot.thermostat.hc1.designtemp,
                        "targetflowtemp": snapshot.thermostat.hc1.targetflowtemp,
                        "minflowtemp": snapshot.thermostat.hc1.minflowtemp,
                        "maxflowtemp": snapshot.thermostat.hc1.maxflowtemp,
                        "heatingtype": snapshot.thermostat.hc1.heatingtype,
                        "summermode": snapshot.thermostat.hc1.summermode,
                        "controlmode": snapshot.thermostat.hc1.controlmode,
                        "nofrostmode": snapshot.thermostat.hc1.nofrostmode,
                        "nofrosttemp": snapshot.thermostat.hc1.nofrosttemp,
                        "program": snapshot.thermostat.hc1.program,
                        "control": snapshot.thermostat.hc1.control,
                    }
                    if snapshot.thermostat.hc1
                    else None
                ),
                "wwk": (
                    {
                        "mode": snapshot.thermostat.wwk.mode,
                        "settemp": snapshot.thermostat.wwk.settemp,
                        "settemplow": snapshot.thermostat.wwk.settemplow,
                        "circmode": snapshot.thermostat.wwk.circmode,
                        "chargeduration": snapshot.thermostat.wwk.chargeduration,
                        "charge": snapshot.thermostat.wwk.charge,
                        "disinfecting": snapshot.thermostat.wwk.disinfecting,
                        "disinfectday": snapshot.thermostat.wwk.disinfectday,
                        "disinfecttime": snapshot.thermostat.wwk.disinfecttime,
                        "dailyheating": snapshot.thermostat.wwk.dailyheating,
                        "dailyheattime": snapshot.thermostat.wwk.dailyheattime,
                        "extra": snapshot.thermostat.wwk.extra,
                    }
                    if snapshot.thermostat.wwk
                    else None
                ),
            }
            if snapshot.thermostat
            else None
        ),
        "prev": prev_values,
        "last_cycles": last_cycles or {},
    }


def extract_prev_values(live_data: dict) -> dict:
    """Extrahiert vorherige Werte aus dem aktuellen Live-Dict für Trend-Anzeige.

    Args:
        live_data: Aktuelles Live-Daten-Dict

    Returns:
        Dict mit vorherigen Werten
    """
    return {
        "outdoor_temp": live_data.get("system", {}).get("outdoor_temp"),
        "flow_temp": live_data.get("boiler", {}).get("flow_temp"),
        "dhw_temp": (live_data.get("dhw") or {}).get("curtemp"),
        "burner_power": live_data.get("boiler", {}).get("burner_power_percent"),
        "pump_modulation": live_data.get("boiler", {}).get("pump_modulation"),
        "energy_total": (live_data.get("consumption") or {}).get(
            "period_energy_total_kwh"
        ),
        "gas_m3": (live_data.get("consumption") or {}).get("period_gas_m3"),
        "mode": live_data.get("mode"),
    }


def _build_errors(error_log: ErrorLog) -> dict:
    """Baut das Fehler-Dict mit None-sicheren Zugriffen."""
    boiler_err = error_log.last_error_by_source("boiler")
    therm_err = error_log.last_error_by_source("thermostat")
    return {
        "count": error_log.count,
        "boiler": {
            "code": boiler_err.code if boiler_err else None,
            "description": boiler_err.description if boiler_err else None,
            "date": boiler_err.error_date if boiler_err else None,
        },
        "thermostat": {
            "code": therm_err.code if therm_err else None,
            "description": therm_err.description if therm_err else None,
            "date": therm_err.error_date if therm_err else None,
        },
    }


def enrich_today_data(today_data: dict, gas_price_per_kwh: float) -> dict:
    """Ergänzt Tagesverbrauch um Kosten.

    Args:
        today_data: Tagesverbrauch aus DB (energy_kwh, heat_kwh, dhw_kwh, ...)
        gas_price_per_kwh: Gaspreis pro kWh

    Returns:
        today_data mit zusätzlichen cost_eur, cost_heat_eur, cost_dhw_eur
    """
    today_data["cost_eur"] = round(today_data["energy_kwh"] * gas_price_per_kwh, 2)
    today_data["cost_heat_eur"] = round(today_data["heat_kwh"] * gas_price_per_kwh, 2)
    today_data["cost_dhw_eur"] = round(today_data["dhw_kwh"] * gas_price_per_kwh, 2)
    return today_data
