"""HeatingController: Zentrale Steuerung der Heizungsanwendung.

Kapselt den Hauptzyklus, alle Manager/Calculators und den
Dashboard-Server in einer Klasse.
"""

import time
import logging

from config.app_config import AppConfig, load_meter_readings
from ..utils.flow_tracer import FlowTracer
from .heating_system_manager import HeatingSystemManager
from .history_buffer import HistoryBuffer
from .db_manager import DBManager, DB_PATH, DB_PATH_SIM
from ..calc.consumption_calc import ConsumptionCalculator, MeterReadings
from ..calc.cost_calc import CostCalculator
from ..calc.runtime_calc import RuntimeCalculator
from ..calc.error_log import ErrorLog
from ..mqttclient import MQTTClient
from ..mqtt_publisher import MQTTPublisher
from ..dashboard_server import DashboardServer
from ..webhooks import WebhookSender
from .live_data_builder import build_live_data, extract_prev_values, enrich_today_data
from .history_writer import HistoryWriter

logger = logging.getLogger(" hc_heat.controller")

# Konstante für Simulate-Tage (wird auch in simulate.py verwendet)
DAYS = 14


def _build_meter_readings() -> MeterReadings:
    """Lädt Zählerstände und baut MeterReadings-Objekt."""
    r = load_meter_readings()
    return MeterReadings(
        nrg_total_start=r["nrg_total_start"],
        nrg_heat_start=r["nrg_heat_start"],
        nrg_dhw_start=r["nrg_dhw_start"],
        energy_year=r["energy_year"],
        gas_total_start=r["gas_total_start"],
        gas_period=r["gas_period"],
    )


class HeatingController:
    """Zentrale Steuerung: Datenerfassung, Berechnung, Dashboard.

    Args:
        config: Gesamtkonfiguration der Anwendung
        running_flag: Callable die True/False zurückgibt (für Shutdown)
    """

    def __init__(self, config: AppConfig, running_flag=None):
        self.config = config
        self._running_flag = running_flag or (lambda: True)

        # Flow-Tracer
        self.tracer = FlowTracer(enabled=config.log.flow_tracer)

        # Manager
        self.manager = HeatingSystemManager(config)

        # DB
        self.db = DBManager(DB_PATH)
        self.db.cleanup()
        self.history_buffer = HistoryBuffer(self.db)

        # Gaszähler einmal beim Start abfragen (für initiale Kosten)
        if self.manager.gasmeter_url:
            self.manager.load_gasmeter(None)
            logger.info("Gaszähler initial geladen")

        # Berechnungsmodule
        readings = _build_meter_readings()
        self.consumption_calc = ConsumptionCalculator(readings)
        self.cost_calc = CostCalculator(config.costs)
        self.runtime_calc = RuntimeCalculator()
        self.error_log = ErrorLog()

        # MQTT (optional)
        self.mqtt_client = MQTTClient(config.mqtt)
        self.mqtt_publisher = MQTTPublisher(self.mqtt_client, config.mqtt)
        if self.mqtt_client.enabled:
            self.mqtt_client.connect()

        # Home Assistant Webhooks (optional)
        self.webhook = WebhookSender(config.ha)

        # History Writer (CSV pro Woche)
        self.history_writer = HistoryWriter(
            history_dir=config.app.history_dir,
            enabled=config.app.save_history,
            keep_weeks=config.app.history_keep_weeks,
        )
        self.history_writer.cleanup()

        # Dashboard Live-Daten Cache
        self._live_data: dict = {}
        self._prev_values: dict = {}
        self._trend_buffer: list[dict] = []  # Ringpuffer für Trend (15 min)
        self._cycle_count: int = 0
        self._last_cycle_date = None

        # Dashboard Server
        self.dashboard = DashboardServer(
            config,
            self._get_live_snapshot,
            self._get_dashboard_config,
            lambda: self.history_buffer.get_last_hours(48),
            self.db.query_daily,
            self._get_kpi_data,
        )

    def _get_live_snapshot(self) -> dict:
        return self._live_data

    def _get_dashboard_config(self) -> dict:
        return {
            "title": self.config.heating.name,
            "manufacturer": self.config.heating.manufacturer,
            "model": self.config.heating.model,
            "installed": self.config.heating.installed,
            "interval": self.config.app.interval,
            "base_path": self.config.app.dashboard_base_path,
            "gas_period": self.config.costs.gas_period,
            "energy_period": self.config.costs.energy_period,
            "gas_price_kwh": self.config.costs.gas_price_per_kwh,
            "gas_price_m3": self.config.costs.gas_price_per_m3,
            "currency": self.config.costs.currency,
        }

    def _get_kpi_data(self) -> dict:
        """KPI-Daten für das zentrale Übersichts-Dashboard."""
        from datetime import datetime

        now = datetime.now()
        live = self._live_data

        # Modus bestimmen
        mode = live.get("mode", "standby")
        boiler = live.get("boiler", {})
        dhw = live.get("dhw", {})
        today = live.get("today", {})

        # Status
        burner_active = boiler.get("burner_active", False)
        status = "ok"

        # Modus-Text für Label
        mode_labels = {
            "heating": "Heizbetrieb",
            "dhw": "Warmwasser",
            "disinfection": "Desinfektion",
            "standby": "Standby",
        }
        mode_text = mode_labels.get(mode, mode)

        # Zusatzinfos
        outdoor_temp = live.get("system", {}).get("outdoor_temp")
        flow_temp = boiler.get("flow_temp")
        dhw_temp = dhw.get("curtemp")

        # Label zusammenbauen
        label_parts = [mode_text]
        if outdoor_temp is not None:
            label_parts.append(f"Außen {outdoor_temp:.0f}°C")
        if burner_active and boiler.get("burner_power_percent"):
            label_parts.append(f"Brenner {boiler['burner_power_percent']}%")
        label = " · ".join(label_parts)

        # Hero: Tagesverbrauch Energie (kWh)
        energy_today = today.get("energy_kwh", 0)

        # Detail: Heizung/WW aufgeteilt
        heat_kwh = today.get("heat_kwh", 0)
        dhw_kwh = today.get("dhw_kwh", 0)
        detail = f"Heute {now.strftime('%d.%m.%Y')} · Heizung {heat_kwh} · WW {dhw_kwh} kWh"

        # Sparkline: letzte 7 Tage energy_kwh
        try:
            daily = self.db.query_daily(7)
            sparkline = [row["energy_kwh"] for row in daily]
        except Exception:
            sparkline = []

        indicator = None
        if sparkline:
            indicator = {
                "type": "sparkline",
                "values": sparkline,
            }

        return {
            "app_id": "hc_heat",
            "app_name": "Heizung",
            "icon": "local_fire_department",
            "url": "http://nuc:5028",
            "status": status,
            "ts": now.isoformat(timespec="seconds"),
            "hero": {
                "value": round(energy_today, 2),
                "unit": "kWh",
                "label": label,
            },
            "detail": detail,
            "indicator": indicator,
            "metrics": [
                {"label": "Heizung", "value": round(heat_kwh, 1), "unit": "kWh"},
                {"label": "WW", "value": round(dhw_kwh, 1), "unit": "kWh"},
                {"label": "Außen", "value": round(outdoor_temp, 1), "unit": "°C"} if outdoor_temp is not None else None,
                {"label": "Vorlauf", "value": round(flow_temp, 1), "unit": "°C"} if flow_temp is not None else None,
            ],
        }

    def run(self) -> None:
        """Hauptschleife: Daten erfassen, berechnen, publizieren."""
        self.dashboard.start()

        logger.info("===  hc_heat Heizungscontroller gestartet ===")
        logger.info("Intervall: %ds", self.config.app.interval)
        logger.info("Heizung: %s", self.config.heating.name)
        logger.info("Boiler URL: %s", self.config.heating.sensor_url)
        if self.config.gasmeter.sensor_url:
            logger.info("Gaszähler URL: %s", self.config.gasmeter.sensor_url)
        if self.mqtt_client.enabled:
            logger.info("MQTT: %s:%d", self.config.mqtt.host, self.config.mqtt.port)
        else:
            logger.info("MQTT: deaktiviert")

        # Webhook nach vollständiger Initialisierung
        self.webhook._send("app_start", {"message": "Heizungscontroller gestartet"})

        # Adaptives Intervall: schneller pollen wenn Brenner aktiv
        _fast = self.config.app.fast_interval   # z.B. 10s
        _slow = self.config.app.interval         # z.B. 60s
        _current_interval = _slow
        _burner_cooldown = 0  # Zähler: nach Brenner-Aus noch X Zyklen schnell pollen

        logger.info("Adaptives Intervall: aktiv=%ds, standby=%ds", _fast, _slow)

        while self._running_flag():
            try:
                self._cycle()

                # Intervall anpassen: schnell wenn Brenner aktiv oder kürzlich aktiv
                boiler = self._live_data.get("boiler", {})
                if boiler.get("burner_active"):
                    _current_interval = _fast
                    _burner_cooldown = 5  # nach Brenner-Aus noch 5 schnelle Zyklen
                elif _burner_cooldown > 0:
                    _current_interval = _fast
                    _burner_cooldown -= 1
                else:
                    _current_interval = _slow

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Fehler im Hauptzyklus: %s", e, exc_info=True)
                _current_interval = _slow

            # Warten
            try:
                for _ in range(_current_interval):
                    if not self._running_flag():
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                break

        self.stop()

    def _cycle(self) -> None:
        """Ein Datenerfassungszyklus."""
        # Zähler um Mitternacht zurücksetzen
        from datetime import datetime
        now = datetime.now()
        if hasattr(self, '_last_cycle_date') and self._last_cycle_date != now.date():
            self._cycle_count = 0
        self._last_cycle_date = now.date()
        self._cycle_count += 1
        self.tracer.trace("app", "Zyklus Start")

        # Snapshot laden
        snapshot = self.manager.load_snapshot()
        self.tracer.trace("app", "Snapshot geladen")

        # Endpoint-Status prüfen und Webhook bei Ausfall
        self.webhook.check_endpoint_status(
            boiler_ok=snapshot.boiler.flow_temp is not None,
            thermostat_ok=snapshot.thermostat is not None and snapshot.thermostat.hc1 is not None,
            gasmeter_ok=snapshot.gas is not None or not self.manager.gasmeter_url,
        )

        # Betriebszustand bestimmen
        state = self.runtime_calc.update(snapshot.boiler)
        logger.debug("Betriebsmodus: %s", state.mode.value)

        # Historie in SQLite speichern
        thc1 = snapshot.thermostat.hc1 if snapshot.thermostat else None
        _hist_data = dict(
            ts=snapshot.timestamp.isoformat(),
            mode=state.mode.value,
            outdoor_temp=snapshot.system.outdoor_temp,
            flow_temp=snapshot.boiler.flow_temp,
            flow_set_temp=snapshot.boiler.flow_set_temp,
            target_flow_temp=thc1.targetflowtemp if thc1 else None,
            dhw_temp=(snapshot.boiler.dhw.curtemp if snapshot.boiler.dhw else None),
            dhw_set_temp=(snapshot.boiler.dhw.settemp if snapshot.boiler.dhw else None),
            burner_active=1 if snapshot.boiler.burner_active else 0,
            burner_power=snapshot.boiler.burner_power_percent,
            pump_active=1 if snapshot.boiler.pump_active else 0,
            pump_modulation=snapshot.boiler.pump_modulation,
            energy_total_kwh=snapshot.boiler.energy_total_kwh,
            energy_heat_kwh=snapshot.boiler.energy_heat_kwh,
            energy_dhw_kwh=snapshot.boiler.energy_dhw_kwh,
            gas_display_m3=snapshot.gas.display_m3 if snapshot.gas else None,
            gas_total_m3=snapshot.gas.total_m3 if snapshot.gas else None,
            burner_starts=snapshot.boiler.burner_starts,
            burner_runtime_min=snapshot.boiler.burner_runtime_min,
            heating_starts=snapshot.boiler.heating_starts,
            heating_runtime_min=snapshot.boiler.heating_runtime_min,
            lastcode_boiler=snapshot.boiler.lastcode,
            lastcode_thermostat=(
                snapshot.thermostat.lastcode if snapshot.thermostat else None
            ),
        )
        self.db.insert(**_hist_data)

        # History CSV schreiben (gleiche Daten, Subset der Spalten)
        self.history_writer.write(**_hist_data)

        # Verbrauch berechnen
        consumption = self.consumption_calc.calculate(
            snapshot.boiler, snapshot.gas, self.runtime_calc.disinfection_ratio()
        )

        # Kosten berechnen
        costs = self.cost_calc.calculate(consumption)

        # Fehler prüfen (Kessel + Thermostat)
        new_error = self.error_log.check_error(snapshot.boiler.lastcode, "boiler")
        if new_error:
            logger.warning("Kessel-Fehler: %s", new_error.description)
        if snapshot.thermostat and snapshot.thermostat.lastcode:
            therm_error = self.error_log.check_error(
                snapshot.thermostat.lastcode, "thermostat"
            )
            if therm_error:
                logger.warning("Thermostat-Fehler: %s", therm_error.description)

        # Home Assistant Webhooks
        _dhw = snapshot.boiler.dhw
        self.webhook.check_and_send(
            mode=state.mode.value,
            error_boiler=snapshot.boiler.lastcode,
            error_thermostat=(
                snapshot.thermostat.lastcode if snapshot.thermostat else None
            ),
            dhw_curtemp=_dhw.curtemp if _dhw else None,
            dhw_flowtempoffset=_dhw.flowtempoffset if _dhw else None,
        )

        # Snapshot speichern (nur wenn aktiviert)
        if self.config.app.save_snapshots:
            from .history_manager import HistoryManager

            _hist = HistoryManager()
            file_path = _hist.save_snapshot(snapshot)
            self.tracer.trace("app", f"Snapshot gespeichert: {file_path.name}")

        # MQTT publizieren (strukturierte Topics)
        if self.mqtt_publisher.enabled:
            self.mqtt_publisher.publish_all(snapshot, state, consumption, costs)
        elif self.mqtt_client._gave_up and not getattr(
            self.mqtt_client, "_gave_up_notified", False
        ):
            self.mqtt_client._gave_up_notified = True
            logger.error("MQTT dauerhaft nicht erreichbar – Webhook gesendet")
            self.webhook._send(
                "mqtt_unavailable",
                {
                    "message": "MQTT Broker nicht erreichbar nach 30 min",
                    "host": self.config.mqtt.host,
                },
            )

        # Vorherige Werte sichern (für Trend – Vergleich mit ~15 min vorher)
        current_vals = extract_prev_values(self._live_data)
        if current_vals.get("outdoor_temp") is not None:
            self._trend_buffer.append(current_vals)
        # Puffer auf max 20 Einträge begrenzen (~20 min bei 60s Intervall)
        max_buf = 20
        if len(self._trend_buffer) > max_buf:
            self._trend_buffer = self._trend_buffer[-max_buf:]
        # Trend-Wert: ältester Eintrag im Puffer (~15-20 min zurück)
        if len(self._trend_buffer) >= 2:
            self._prev_values = self._trend_buffer[0]
        else:
            self._prev_values = current_vals

        # Tagesverbrauch mit Kosten
        today_data = self.db.query_today_delta()
        enrich_today_data(today_data, self.config.costs.gas_price_per_kwh)

        # Live-Daten für Dashboard aktualisieren
        new_data = build_live_data(
            snapshot=snapshot,
            state=state,
            consumption=consumption,
            costs=costs,
            error_log=self.error_log,
            today_data=today_data,
            prev_values=self._prev_values.copy(),
            last_cycles=self.db.query_last_cycles(),
        )
        self._live_data.clear()
        self._live_data.update(new_data)
        self._live_data["cycle_count"] = self._cycle_count

        # Log-Ausgabe
        b = snapshot.boiler
        dhw = b.dhw
        logger.info(
            "Mode=%s | Outdoor=%.1f°C | Flow=%.1f°C | Burner=%s | DHW=%.1f°C",
            state.mode.value,
            snapshot.system.outdoor_temp or 0,
            b.flow_temp or 0,
            b.burner_active,
            (dhw.curtemp if dhw else 0) or 0,
        )

        self.tracer.trace("app", "Zyklus Ende")

    def run_simulate(self) -> None:
        """Startet nur das Dashboard mit Simulate-Daten (kein HTTP-Abruf).

        Springt automatisch alle 5 Sekunden zum nächsten Moduswechsel,
        damit alle Status (heating, dhw, disinfection, standby) im
        Flussdiagramm getestet werden können.
        """
        logger.info("=== SIMULATE MODUS – nur Dashboard ===")

        db = DBManager(DB_PATH_SIM)
        if db.count() == 0:
            logger.error("Keine Simulate-Daten! Erst 'make simulate' ausführen.")
            return

        logger.info("DB: %s (%d Zeilen)", DB_PATH_SIM.name, db.count())
        history_buffer = HistoryBuffer(db)

        # Alle Datenpunkte laden – je einen repräsentativen pro Modus finden
        _all = db.query_all()
        seen_modes = {}
        for row in _all:
            m = row.get("mode") or "standby"
            if m not in seen_modes:
                seen_modes[m] = row
        transitions = list(seen_modes.values())

        # Gewünschte Reihenfolge
        mode_order = ["standby", "heating", "dhw", "disinfection"]
        transitions = sorted(transitions, key=lambda r: mode_order.index(r.get("mode", "standby")) if r.get("mode") in mode_order else 99)

        logger.info("Simulate-Modi: %d (%s)", len(transitions), ", ".join(seen_modes.keys()))

        today = db.query_today_delta()
        _gpk = self.config.costs.gas_price_per_kwh
        today["cost_eur"] = round(today["energy_kwh"] * _gpk, 2)
        today["cost_heat_eur"] = round(today["heat_kwh"] * _gpk, 2)
        today["cost_dhw_eur"] = round(today["dhw_kwh"] * _gpk, 2)

        # Perioden-Verbrauch
        if len(_all) >= 2:
            _first, _last = _all[0], _all[-1]
            _pe = round((_last["energy_total_kwh"] or 0) - (_first["energy_total_kwh"] or 0), 1)
            _ph = round((_last["energy_heat_kwh"] or 0) - (_first["energy_heat_kwh"] or 0), 1)
            _pd = round((_last["energy_dhw_kwh"] or 0) - (_first["energy_dhw_kwh"] or 0), 1)
            _pg = round((_last["gas_display_m3"] or 0) - (_first["gas_display_m3"] or 0), 1)
        else:
            _pe = _ph = _pd = _pg = 0

        _sim_consumption = {
            "energy_total_kwh": (_all[-1]["energy_total_kwh"] if _all else 0),
            "energy_heat_kwh": (_all[-1]["energy_heat_kwh"] if _all else 0),
            "energy_dhw_kwh": (_all[-1]["energy_dhw_kwh"] if _all else 0),
            "period_energy_total_kwh": _pe,
            "period_energy_heat_kwh": _ph,
            "period_energy_dhw_kwh": _pd,
            "period_energy_dhw_only_kwh": _pd,
            "period_energy_disinfection_kwh": 0,
            "period_gas_m3": _pg,
            "burner_starts": (_all[-1].get("burner_starts") if _all else 0),
            "burner_runtime_min": (_all[-1].get("burner_runtime_min") if _all else 0),
            "heating_starts": (_all[-1].get("heating_starts") if _all else 0),
            "heating_runtime_min": (_all[-1].get("heating_runtime_min") if _all else 0),
            "dhw_runtime_min": max(0, ((_all[-1].get("burner_runtime_min") or 0) - ((_all[-1].get("heating_runtime_min")) or 0)) if _all else 0),
            "dhw_starts": max(0, ((_all[-1].get("burner_starts") or 0) - ((_all[-1].get("heating_starts")) or 0)) if _all else 0),
            "disinfection_ratio": 0,
        }
        _sim_costs = {
            "gas_total_eur": round(_pg * self.config.costs.gas_price_per_m3, 2),
            "energy_total_eur": round(_pe * self.config.costs.gas_price_per_kwh, 2),
            "energy_heat_eur": round(_ph * self.config.costs.gas_price_per_kwh, 2),
            "energy_dhw_eur": round(_pd * self.config.costs.gas_price_per_kwh, 2),
            "energy_dhw_only_eur": round(_pd * self.config.costs.gas_price_per_kwh, 2),
            "energy_disinfection_eur": 0,
            "gas_period": self.config.costs.gas_period,
            "energy_period": self.config.costs.energy_period,
            "currency": self.config.costs.currency,
        }

        # Aktueller Index in transitions (Thread-safe via Liste)
        _idx = [0]

        def _build_live(r: dict) -> dict:
            """Baut Live-Daten aus einem Datenpunkt."""
            return {
                "today": today,
                "timestamp": r["ts"],
                "mode": r["mode"] or "standby",
                "mode_duration_sec": 300,
                "system": {
                    "outdoor_temp": r["outdoor_temp"],
                    "heating_active": r["mode"] == "heating",
                    "heating_off": False,
                    "tapwater_active": r["mode"] == "dhw",
                    "curve_on": False,
                    "summer_temp": 16,
                    "frost_mode": False,
                },
                "boiler": {
                    "flow_temp": r["flow_temp"],
                    "flow_set_temp": r["flow_set_temp"],
                    "outdoor_temp": r["outdoor_temp"],
                    "burner_active": bool(r["burner_active"]),
                    "heating_active": r["mode"] == "heating",
                    "heating_enabled": True,
                    "burner_power_percent": r["burner_power"],
                    "flame_current": 0,
                    "nominal_power_kw": 14,
                    "current_power_kw": (r["burner_power"] or 0) / 100 * 14,
                    "pump_active": bool(r["pump_active"]),
                    "pump_modulation": r["pump_modulation"] or 37,
                    "pump_mode": "deltaP-2",
                    "pump_min": 10,
                    "pump_max": 100,
                    "lastcode": r.get("lastcode_boiler"),
                    "service_code": "0Y",
                    "service_code_number": 204,
                    "maintenance_date": None,
                },
                "dhw": {
                    "curtemp": r["dhw_temp"],
                    "settemp": r["dhw_set_temp"],
                    "active": r["mode"] == "dhw",
                    "charging": r["mode"] == "dhw",
                    "tempok": True,
                    "disinfecting": r["mode"] == "disinfection",
                    "disinfection_temp": 70,
                    "comfort": "Eco",
                    "storage_type": "Speicher",
                    "flowtempoffset": 40,
                },
                "heating_circuit": {
                    "flow_temp": r["flow_temp"],
                    "return_temp": None,
                    "set_flow_temp": r["flow_set_temp"],
                    "pump_active": r["mode"] == "heating",
                },
                "gas": {
                    "display_m3": r["gas_display_m3"],
                    "total_m3": r.get("gas_total_m3"),
                    "timestamp": r["ts"],
                },
                "consumption": _sim_consumption,
                "costs": _sim_costs,
                "errors": {
                    "count": 0,
                    "boiler": {"code": None, "description": None, "date": None},
                    "thermostat": {"code": None, "description": None, "date": None},
                },
                "prev": {},
            }

        _live_data = _build_live(transitions[0])

        def _get_live() -> dict:
            return _live_data

        def _get_config() -> dict:
            return {
                "title": self.config.heating.name + " [SIMULATE]",
                "manufacturer": self.config.heating.manufacturer,
                "model": self.config.heating.model,
                "installed": self.config.heating.installed,
                "interval": 5,
                "currency": self.config.costs.currency,
            }

        dashboard = DashboardServer(
            self.config,
            _get_live,
            _get_config,
            lambda: history_buffer.get_last_hours(24 * DAYS),
            db.query_daily,
        )
        dashboard.start()

        logger.info(
            "Dashboard: http://0.0.0.0:%d/dashboardhaco",
            self.config.app.dashboard_port,
        )
        logger.info("Simulate: %d Moduswechsel, wechselt alle 5s", len(transitions))
        logger.info("Ctrl+C zum Beenden")

        step_interval = 5  # Sekunden pro Schritt
        step_counter = 0
        while self._running_flag():
            time.sleep(1)
            step_counter += 1
            if step_counter >= step_interval:
                step_counter = 0
                _idx[0] = (_idx[0] + 1) % len(transitions)
                r = transitions[_idx[0]]
                _live_data.clear()
                _live_data.update(_build_live(r))
                logger.info("→ Simulate [%d/%d]: %s (%s)",
                            _idx[0] + 1, len(transitions), r["mode"], r["ts"][:19])

        dashboard.stop()
        logger.info("=== SIMULATE beendet ===")

    def stop(self) -> None:
        """Aufräumen: Dashboard stoppen, MQTT trennen."""
        self.webhook._send("app_stop", {"message": "Heizungscontroller beendet"})
        self.dashboard.stop()
        self.mqtt_client.disconnect()
        logger.info("===  hc_heat beendet ===")
