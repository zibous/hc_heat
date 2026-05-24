"""Desinfektions-Datenmodell (aus dhw-Daten abgeleitet)."""

from dataclasses import dataclass
from typing import Optional

from ..utils.field_mapper import mapped_get
from ..utils.helpers import to_float, to_bool, to_int

_S = "dhw"  # Nutzt DHW-Mapping-Sektion


@dataclass
class Disinfection:
    """Desinfektionszyklus-Daten, extrahiert aus dem dhw-Objekt."""

    active: Optional[bool] = None
    disinfection_temp: Optional[float] = None
    curtemp: Optional[float] = None
    starts: Optional[int] = None
    workm: Optional[int] = None

    @classmethod
    def from_dhw(cls, dhw_data: dict) -> "Disinfection":
        """Erstellt Disinfection aus dem dhw-Unterobjekt."""
        d = dhw_data or {}
        g = lambda name, default=None: mapped_get(d, name, _S, default)
        return cls(
            active=to_bool(g("disinfecting")),
            disinfection_temp=to_float(g("disinfection_temp")),
            curtemp=to_float(g("curtemp")),
            starts=to_int(g("starts")),
            workm=to_int(g("workm")),
        )
