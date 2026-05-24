"""System-Daten: Allgemeine Heizungsparameter aus der Boiler-API."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..utils.field_mapper import mapped_get
from ..utils.helpers import to_float, to_bool

_S = "system"  # Mapping-Sektion


@dataclass
class SystemData:
    """Systemweite Heizungsparameter."""

    outdoor_temp: Optional[float] = None
    heating_off: Optional[bool] = None
    heating_active: Optional[bool] = None
    tapwater_active: Optional[bool] = None

    curve_on: Optional[bool] = None
    curve_base: Optional[float] = None
    curve_end: Optional[float] = None

    summer_temp: Optional[float] = None
    frost_mode: Optional[bool] = None
    frost_temp: Optional[float] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "SystemData":
        """Erstellt SystemData aus der Boiler-API Antwort."""
        d = data or {}
        g = lambda name, default=None: mapped_get(d, name, _S, default)
        return cls(
            outdoor_temp=to_float(g("outdoor_temp")),
            heating_off=to_bool(g("heating_off")),
            heating_active=to_bool(g("heating_active")),
            tapwater_active=to_bool(g("tapwater_active")),
            curve_on=to_bool(g("curve_on")),
            curve_base=to_float(g("curve_base")),
            curve_end=to_float(g("curve_end")),
            summer_temp=to_float(g("summer_temp")),
            frost_mode=to_bool(g("frost_mode")),
            frost_temp=to_float(g("frost_temp")),
            raw=d,
        )
