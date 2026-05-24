"""Verbrauchsberechnung nach Betriebsart – kumulativ und pro Periode."""

import logging
from dataclasses import dataclass
from typing import Optional

from ..models.boiler import Boiler
from ..models.gas_meter import GasMeter

logger = logging.getLogger("hc_haco2.calc.consumption")


@dataclass
class ConsumptionResult:
    """Verbrauchswerte aufgeteilt nach Betriebsart."""

    # Energie kWh (kumulativ vom Gerät seit Installation)
    energy_total_kwh: float = 0.0
    energy_heat_kwh: float = 0.0
    energy_dhw_kwh: float = 0.0  # WW + Desinfektion zusammen
    energy_dhw_only_kwh: float = 0.0  # nur WW (geschätzt)
    energy_disinfection_kwh: float = 0.0  # nur Desinfektion (geschätzt)

    # Energie kWh (Periode)
    period_energy_total_kwh: float = 0.0
    period_energy_heat_kwh: float = 0.0
    period_energy_dhw_kwh: float = 0.0  # WW + Desinfektion
    period_energy_dhw_only_kwh: float = 0.0  # nur WW (geschätzt)
    period_energy_disinfection_kwh: float = 0.0  # nur Desinfektion (geschätzt)

    # Gas m³
    gas_total_m3: float = 0.0
    period_gas_m3: float = 0.0

    # Laufzeiten Minuten (vom Gerät)
    burner_runtime_min: int = 0
    heating_runtime_min: int = 0
    dhw_runtime_min: int = 0  # WW + Desinfektion (berechnet)

    # Starts (vom Gerät)
    burner_starts: int = 0
    heating_starts: int = 0
    dhw_starts: int = 0  # WW + Desinfektion (berechnet)

    # Desinfektions-Anteil (0.0 - 1.0)
    disinfection_ratio: float = 0.0


@dataclass
class MeterReadings:
    """Zählerstände zu Beginn der aktuellen Abrechnungsperioden."""

    nrg_total_start: float = 0.0
    nrg_heat_start: float = 0.0
    nrg_dhw_start: float = 0.0
    energy_year: int = 0
    gas_total_start: float = 0.0
    gas_period: str = ""


class ConsumptionCalculator:
    """Berechnet Verbrauchskennzahlen aus Boiler-Daten."""

    def __init__(self, readings: Optional[MeterReadings] = None):
        self.readings = readings or MeterReadings()

    def calculate(
        self,
        boiler: Boiler,
        gas: Optional[GasMeter] = None,
        disinfection_ratio: float = 0.0,
    ) -> ConsumptionResult:
        """Berechnet kumulative und Perioden-Verbrauchswerte.

        Args:
            disinfection_ratio: Anteil Desinfektion an DHW-Energie (0.0-1.0),
                                kommt vom RuntimeCalculator.
        """
        total = boiler.energy_total_kwh or 0.0
        heat = boiler.energy_heat_kwh or 0.0
        dhw = boiler.energy_dhw_kwh or 0.0
        gas_m3 = gas.display_m3 if gas and gas.display_m3 else 0.0

        r = self.readings
        dr = min(max(disinfection_ratio, 0.0), 1.0)

        # Perioden-Werte
        p_total = max(0.0, total - r.nrg_total_start)
        p_heat = max(0.0, heat - r.nrg_heat_start)
        p_dhw = max(0.0, dhw - r.nrg_dhw_start)

        # DHW aufteilen in WW-only und Desinfektion
        dhw_only = dhw * (1.0 - dr)
        dhw_dis = dhw * dr
        p_dhw_only = p_dhw * (1.0 - dr)
        p_dhw_dis = p_dhw * dr

        # Laufzeiten
        burner_min = boiler.burner_runtime_min or 0
        heat_min = boiler.heating_runtime_min or 0
        dhw_min = max(0, burner_min - heat_min)
        dhw_starts = max(0, (boiler.burner_starts or 0) - (boiler.heating_starts or 0))

        return ConsumptionResult(
            energy_total_kwh=total,
            energy_heat_kwh=heat,
            energy_dhw_kwh=dhw,
            energy_dhw_only_kwh=dhw_only,
            energy_disinfection_kwh=dhw_dis,
            period_energy_total_kwh=p_total,
            period_energy_heat_kwh=p_heat,
            period_energy_dhw_kwh=p_dhw,
            period_energy_dhw_only_kwh=p_dhw_only,
            period_energy_disinfection_kwh=p_dhw_dis,
            gas_total_m3=gas_m3,
            period_gas_m3=max(0.0, gas_m3 - r.gas_total_start),
            burner_runtime_min=burner_min,
            heating_runtime_min=heat_min,
            dhw_runtime_min=dhw_min,
            burner_starts=boiler.burner_starts or 0,
            heating_starts=boiler.heating_starts or 0,
            dhw_starts=dhw_starts,
            disinfection_ratio=dr,
        )
