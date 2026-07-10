# -*- coding: utf-8 -*-
"""MQTT Publisher – strukturierte Topics pro Betriebsbereich.

Topic-Struktur:
  {base}/status    → App-Status (uptime, cycle, mode, errors)
  {base}/boiler    → Kessel (Temperaturen, Brenner, Pumpe, Fehler)
  {base}/dhw       → Warmwasser (Temperatur, Ladung, Desinfektion)
  {base}/heating   → Heizbetrieb (Vorlauf, Außentemp, Sollwerte)
  {base}/energy    → Energie/Gas Verbrauch pro Periode
  {base}/costs     → Kosten pro Periode
  {base}/gas       → Gaszähler (m³, kWh)
"""

import logging
from datetime import datetime

from .mqttclient import MQTTClient
from .models.heating_snapshot import HeatingSnapshot
from .models.operation_state import OperationState
from .calc.consumption_calc import ConsumptionResult
from .calc.cost_calc import CostResult
from config.app_config import MQTTSettings

logger = logging.getLogger(" hc_heat.mqtt_pub")


class MQTTPublisher:
    """Publiziert Heizungsdaten auf strukturierte MQTT Topics."""

    def __init__(self, client: MQTTClient, settings: MQTTSettings):
        self.client = client
        self.settings = settings
        self._cycle_count = 0
        self._start_time = datetime.now().astimezone()

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    def publish_all(
        self,
        snapshot: HeatingSnapshot,
        state: OperationState,
        consumption: ConsumptionResult,
        costs: CostResult,
    ) -> None:
        """Publiziert alle Topics in einem Zyklus."""
        if not self.enabled:
            return
        self._cycle_count += 1

        self._publish_status(snapshot, state)
        self._publish_boiler(snapshot)
        self._publish_dhw(snapshot)
        self._publish_heating(snapshot)
        self._publish_energy(consumption)
        self._publish_costs(costs)
        self._publish_gas(snapshot, consumption)

    def _publish_status(self, snap: HeatingSnapshot, state: OperationState) -> None:
        uptime_min = int((datetime.now().astimezone() - self._start_time).total_seconds() / 60)
        self.client.publish(
            self.settings.topic_status,
            {
                "timestamp": snap.timestamp.isoformat(),
                "mode": state.mode.value,
                "mode_since": state.start.isoformat(),
                "cycle": self._cycle_count,
                "uptime_min": uptime_min,
                "error_boiler": snap.boiler.lastcode,
                "error_thermostat": (
                    snap.thermostat.lastcode if snap.thermostat else None
                ),
                "service_code": snap.boiler.service_code,
            },
        )

    def _publish_boiler(self, snap: HeatingSnapshot) -> None:
        b = snap.boiler
        self.client.publish(
            self.settings.topic_boiler,
            {
                "flow_temp": b.flow_temp,
                "flow_set_temp": b.flow_set_temp,
                "outdoor_temp": b.outdoor_temp,
                "burner_active": b.burner_active,
                "burner_power_pct": b.burner_power_percent,
                "burner_power_kw": b.current_power_kw(),
                "pump_active": b.pump_active,
                "pump_modulation": b.pump_modulation,
                "flame_current": b.flame_current,
                "burner_starts": b.burner_starts,
                "burner_runtime_h": round((b.burner_runtime_min or 0) / 60, 1),
                "heating_active": b.heating_active,
                "tapwater_active": b.tapwater_active,
            },
        )

    def _publish_dhw(self, snap: HeatingSnapshot) -> None:
        b = snap.boiler
        dhw = b.dhw
        dis = b.disinfection
        self.client.publish(
            self.settings.topic_dhw,
            {
                "temp": dhw.curtemp if dhw else None,
                "set_temp": dhw.settemp if dhw else None,
                "charging": dhw.charging if dhw else False,
                "active": dhw.active if dhw else False,
                "tapwater_active": b.tapwater_active,
                "disinfecting": dis.active if dis else False,
                "disinfection_temp": dis.disinfection_temp if dis else None,
                "flow_temp_offset": dhw.flowtempoffset if dhw else None,
                "threeway_valve": dhw.threeway_valve if dhw else None,
            },
        )

    def _publish_heating(self, snap: HeatingSnapshot) -> None:
        b = snap.boiler
        t = snap.thermostat
        hc1 = t.hc1 if t else None
        self.client.publish(
            self.settings.topic_heating,
            {
                "outdoor_temp": b.outdoor_temp,
                "flow_temp": b.flow_temp,
                "flow_set_temp": b.flow_set_temp,
                "heating_active": b.heating_active,
                "target_flow_temp": hc1.targetflowtemp if hc1 else None,
                "sel_room_temp": hc1.seltemp if hc1 else None,
                "thermostat_mode": hc1.mode if hc1 else None,
                "summer_mode": hc1.summermode if hc1 else None,
                "damped_outdoor_temp": t.damped_outdoor_temp if t else None,
            },
        )

    def _publish_energy(self, c: ConsumptionResult) -> None:
        self.client.publish(
            self.settings.topic_energy,
            {
                "total_kwh": round(c.energy_total_kwh, 2),
                "heat_kwh": round(c.energy_heat_kwh, 2),
                "dhw_kwh": round(c.energy_dhw_kwh, 2),
                "dhw_only_kwh": round(c.energy_dhw_only_kwh, 2),
                "disinfection_kwh": round(c.energy_disinfection_kwh, 2),
                "period_total_kwh": round(c.period_energy_total_kwh, 2),
                "period_heat_kwh": round(c.period_energy_heat_kwh, 2),
                "period_dhw_kwh": round(c.period_energy_dhw_kwh, 2),
                "burner_runtime_h": round(c.burner_runtime_min / 60, 1),
                "heating_runtime_h": round(c.heating_runtime_min / 60, 1),
                "dhw_runtime_h": round(c.dhw_runtime_min / 60, 1),
                "burner_starts": c.burner_starts,
                "heating_starts": c.heating_starts,
            },
        )

    def _publish_costs(self, costs: CostResult) -> None:
        self.client.publish(
            self.settings.topic_costs,
            {
                "gas_eur": round(costs.gas_total_eur, 2),
                "gas_period": costs.gas_period,
                "energy_total_eur": round(costs.energy_total_eur, 2),
                "energy_heat_eur": round(costs.energy_heat_eur, 2),
                "energy_dhw_eur": round(costs.energy_dhw_eur, 2),
                "energy_period": costs.energy_period,
                "currency": costs.currency,
            },
        )

    def _publish_gas(self, snap: HeatingSnapshot, c: ConsumptionResult) -> None:
        gas = snap.gas
        self.client.publish(
            self.settings.topic_gas,
            {
                "display_m3": gas.display_m3 if gas else None,
                "total_m3": gas.total_m3 if gas else None,
                "period_m3": round(c.period_gas_m3, 3),
                "timestamp": gas.timestamp if gas else None,
            },
        )

    def disconnect(self) -> None:
        self.client.disconnect()
