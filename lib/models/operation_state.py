"""Betriebszustand-Tracking für Laufzeitberechnung."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class OperationMode(Enum):
    """Betriebsarten der Heizungsanlage."""

    STANDBY = "standby"
    HEATING = "heating"
    DHW = "dhw"
    DISINFECTION = "disinfection"


@dataclass
class OperationState:
    """Ein Betriebszustand mit Start- und Endzeit."""

    mode: OperationMode
    start: datetime
    end: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Dauer in Sekunden (0 wenn noch aktiv)."""
        if self.end is None:
            return 0.0
        return (self.end - self.start).total_seconds()

    @property
    def is_active(self) -> bool:
        return self.end is None
