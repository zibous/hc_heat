"""Kostenberechnung für Gas und Energie – pro Abrechnungsperiode."""

import logging
from dataclasses import dataclass

from config.app_config import CostSettings
from .consumption_calc import ConsumptionResult

logger = logging.getLogger(" hc_heat.calc.cost")


@dataclass
class CostResult:
    """Berechnete Kosten pro Abrechnungsperiode."""

    gas_total_eur: float = 0.0
    gas_period: str = ""

    energy_total_eur: float = 0.0
    energy_heat_eur: float = 0.0
    energy_dhw_eur: float = 0.0
    energy_dhw_only_eur: float = 0.0
    energy_disinfection_eur: float = 0.0
    energy_period: str = ""

    currency: str = "EUR"


class CostCalculator:
    """Berechnet Kosten basierend auf Periodenverbrauch."""

    def __init__(self, costs: CostSettings):
        self.costs = costs

    def calculate(self, consumption: ConsumptionResult) -> CostResult:
        c = self.costs
        return CostResult(
            gas_total_eur=consumption.period_gas_m3 * c.gas_price_per_m3,
            gas_period=c.gas_period,
            energy_total_eur=consumption.period_energy_total_kwh * c.gas_price_per_kwh,
            energy_heat_eur=consumption.period_energy_heat_kwh * c.gas_price_per_kwh,
            energy_dhw_eur=consumption.period_energy_dhw_kwh * c.gas_price_per_kwh,
            energy_dhw_only_eur=consumption.period_energy_dhw_only_kwh
            * c.gas_price_per_kwh,
            energy_disinfection_eur=consumption.period_energy_disinfection_kwh
            * c.gas_price_per_kwh,
            energy_period=c.energy_period,
            currency=c.currency,
        )
