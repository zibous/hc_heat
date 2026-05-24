"""Snapshot: Vollständiger Systemzustand zu einem Zeitpunkt."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .system_data import SystemData
from .boiler import Boiler
from .heating_circuit import HeatingCircuit
from .gas_meter import GasMeter
from .thermostat import Thermostat


@dataclass
class HeatingSnapshot:
    """Kompletter Heizungs-Snapshot für Persistierung."""

    timestamp: datetime
    system: SystemData
    boiler: Boiler
    heating: HeatingCircuit
    gas: Optional[GasMeter] = None
    thermostat: Optional[Thermostat] = None
