"""Heizkreis-Datenmodell."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..utils.field_mapper import mapped_get
from ..utils.helpers import to_float, to_bool, to_int

_S = "heating_circuit"  # Mapping-Sektion


@dataclass
class HeatingCircuit:
    """Heizkreis-Daten (Vorlauf, Rücklauf, Pumpe)."""

    flow_temp: Optional[float] = None
    return_temp: Optional[float] = None
    set_flow_temp: Optional[float] = None
    mode: Optional[str] = None
    pump_active: Optional[bool] = None
    pump_modulation: Optional[int] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "HeatingCircuit":
        """Erstellt HeatingCircuit aus der Boiler-API Antwort."""
        d = data or {}
        g = lambda name, default=None: mapped_get(d, name, _S, default)
        return cls(
            flow_temp=to_float(g("flow_temp")),
            return_temp=to_float(g("return_temp")),
            set_flow_temp=to_float(g("set_flow_temp")),
            mode=g("mode"),
            pump_active=to_bool(g("pump_active")),
            pump_modulation=to_int(g("pump_modulation")),
            raw=d,
        )
