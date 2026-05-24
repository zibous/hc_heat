"""Warmwasser (Domestic Hot Water) Datenmodell."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..utils.field_mapper import mapped_get
from ..utils.helpers import to_float, to_bool, to_int

_S = "dhw"  # Mapping-Sektion


@dataclass
class DHW:
    """Warmwasser-Speicher Daten aus dem EMS-ESP dhw-Objekt."""

    curtemp: Optional[float] = None
    curtemp2: Optional[float] = None
    settemp: Optional[float] = None
    seltemp: Optional[float] = None
    flowtempoffset: Optional[float] = None
    comfort: Optional[str] = None
    storage_type: Optional[str] = None
    charge_type: Optional[str] = None

    activated: Optional[bool] = None
    active: Optional[bool] = None
    charging: Optional[bool] = None
    recharging: Optional[bool] = None
    tempok: Optional[bool] = None
    onetime: Optional[bool] = None
    threeway_valve: Optional[bool] = None
    chargepump: Optional[bool] = None
    circpump: Optional[bool] = None

    disinfecting: Optional[bool] = None
    disinfection_temp: Optional[float] = None

    starts: Optional[int] = None
    workm: Optional[int] = None
    nrg: Optional[float] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, dhw_data: dict) -> "DHW":
        """Erstellt DHW aus dem dhw-Unterobjekt der Boiler-API."""
        d = dhw_data or {}
        g = lambda name, default=None: mapped_get(d, name, _S, default)
        return cls(
            curtemp=to_float(g("curtemp")),
            curtemp2=to_float(g("curtemp2")),
            settemp=to_float(g("settemp")),
            seltemp=to_float(g("seltemp")),
            flowtempoffset=to_float(g("flowtempoffset")),
            comfort=g("comfort"),
            storage_type=g("storage_type"),
            charge_type=g("charge_type"),
            activated=to_bool(g("activated")),
            active=to_bool(g("active")),
            charging=to_bool(g("charging")),
            recharging=to_bool(g("recharging")),
            tempok=to_bool(g("tempok")),
            onetime=to_bool(g("onetime")),
            threeway_valve=to_bool(g("threeway_valve")),
            chargepump=to_bool(g("chargepump")),
            circpump=to_bool(g("circpump")),
            disinfecting=to_bool(g("disinfecting")),
            disinfection_temp=to_float(g("disinfection_temp")),
            starts=to_int(g("starts")),
            workm=to_int(g("workm")),
            nrg=to_float(g("nrg")),
            raw=d,
        )
