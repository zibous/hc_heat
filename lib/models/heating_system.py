"""HeatingSystem: Container für alle Heizungskomponenten."""

from dataclasses import dataclass
from typing import Optional

from .system_data import SystemData
from .boiler import Boiler
from .heating_circuit import HeatingCircuit
from .gas_meter import GasMeter
from .thermostat import Thermostat


@dataclass
class HeatingSystem:
    """Aktueller Zustand aller Heizungskomponenten."""

    system: SystemData
    boiler: Boiler
    heating: HeatingCircuit
    gas: Optional[GasMeter] = None
    thermostat: Optional[Thermostat] = None
