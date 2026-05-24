"""Boiler/Kessel Datenmodell – Hauptdatenquelle aus /api/boiler."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .dhw import DHW
from .disinfection import Disinfection
from ..utils.field_mapper import mapped_get
from ..utils.helpers import to_float, to_bool, to_int

_S = "boiler"  # Mapping-Sektion


@dataclass
class Boiler:
    """Kessel-Daten aus der EMS-ESP Boiler-API."""

    # Temperaturen
    flow_temp: Optional[float] = None
    flow_set_temp: Optional[float] = None
    outdoor_temp: Optional[float] = None

    # Brennerstatus
    burner_active: Optional[bool] = None
    burner_active2: Optional[bool] = None
    heating_active: Optional[bool] = None
    heating_enabled: Optional[bool] = None
    tapwater_active: Optional[bool] = None

    # Brennerleistung
    burner_power_percent: Optional[int] = None
    burner_power_set: Optional[int] = None
    flame_current: Optional[float] = None
    nominal_power_kw: Optional[int] = None

    # Pumpen
    pump_active: Optional[bool] = None
    pump_modulation: Optional[int] = None
    pump_mode: Optional[str] = None
    pump_min: Optional[int] = None
    pump_max: Optional[int] = None

    # Unterobjekte
    dhw: Optional[DHW] = None
    disinfection: Optional[Disinfection] = None

    # Energie (kumulativ vom Gerät)
    energy_total_kwh: Optional[float] = None
    energy_heat_kwh: Optional[float] = None
    energy_dhw_kwh: Optional[float] = None

    # Laufzeiten
    burner_starts: Optional[int] = None
    burner_runtime_min: Optional[int] = None
    heating_runtime_min: Optional[int] = None
    heating_starts: Optional[int] = None
    uptime_sec: Optional[int] = None

    # Fehler / Service
    lastcode: Optional[str] = None
    service_code: Optional[str] = None
    service_code_number: Optional[int] = None
    maintenance_message: Optional[str] = None
    maintenance_date: Optional[str] = None

    # Rohdaten
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "Boiler":
        """Erstellt Boiler aus der /api/boiler Antwort."""
        d = data or {}
        g = lambda name, default=None: mapped_get(d, name, _S, default)
        dhw_data = d.get("dhw") or {}

        return cls(
            flow_temp=to_float(g("flow_temp")),
            flow_set_temp=to_float(g("flow_set_temp")),
            outdoor_temp=to_float(g("outdoor_temp")),
            burner_active=to_bool(g("burner_active")),
            burner_active2=to_bool(g("burner_active2")),
            heating_active=to_bool(g("heating_active")),
            heating_enabled=to_bool(g("heating_enabled")),
            tapwater_active=to_bool(g("tapwater_active")),
            burner_power_percent=to_int(g("burner_power_percent")),
            burner_power_set=to_int(g("burner_power_set")),
            flame_current=to_float(g("flame_current")),
            nominal_power_kw=to_int(g("nominal_power_kw")),
            pump_active=to_bool(g("pump_active")),
            pump_modulation=to_int(g("pump_modulation")),
            pump_mode=g("pump_mode"),
            pump_min=to_int(g("pump_min")),
            pump_max=to_int(g("pump_max")),
            dhw=DHW.from_api(dhw_data),
            disinfection=Disinfection.from_dhw(dhw_data),
            energy_total_kwh=to_float(g("energy_total_kwh")),
            energy_heat_kwh=to_float(g("energy_heat_kwh")),
            energy_dhw_kwh=to_float(dhw_data.get("nrg")),
            burner_starts=to_int(g("burner_starts")),
            burner_runtime_min=to_int(g("burner_runtime_min")),
            heating_runtime_min=to_int(g("heating_runtime_min")),
            heating_starts=to_int(g("heating_starts")),
            uptime_sec=to_int(g("uptime_sec")),
            lastcode=g("lastcode"),
            service_code=g("service_code"),
            service_code_number=to_int(g("service_code_number")),
            maintenance_message=g("maintenance_message"),
            maintenance_date=g("maintenance_date"),
            raw=d,
        )

    def current_power_kw(self) -> Optional[float]:
        """Aktuelle Brennerleistung in kW."""
        if self.burner_power_percent is None or self.nominal_power_kw is None:
            return None
        return (self.burner_power_percent / 100) * self.nominal_power_kw
