""" hc_heat – Heizungscontroller Hauptanwendung.

Erfasst Heizungsdaten, berechnet Kennzahlen, speichert Snapshots
und publiziert optional per MQTT.
"""

import sys
import signal
import logging
from pathlib import Path

# .env laden (einfach, ohne python-dotenv Abhängigkeit)
from lib.utils.env_loader import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from config.app_config import load_config, load_meter_readings
from lib.utils.logging_setup import setup_logging
from lib.core.heating_system_manager import HeatingSystemManager
from lib.calc.consumption_calc import ConsumptionCalculator, MeterReadings
from lib.calc.cost_calc import CostCalculator
from lib.calc.runtime_calc import RuntimeCalculator
from lib.core.controller import HeatingController

logger = logging.getLogger(" hc_heat.app")

# Graceful Shutdown
_running = True


def _signal_handler(sig: int, frame: object) -> None:
    global _running
    logger.info("Signal %d empfangen – beende...", sig)
    _running = False
    # Zweites Signal = sofort beenden
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(1))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(1))


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


def _print_section(title: str) -> None:
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def _print_kv(key: str, value: object, unit: str = "") -> None:
    if value is None:
        print(f"  {key:<35} —")
    elif unit:
        print(f"  {key:<35} {value} {unit}")
    else:
        print(f"  {key:<35} {value}")


def run_once() -> None:
    """Einmaliger Abruf mit detaillierter Ausgabe aller Daten."""
    config = load_config()
    setup_logging(config.log)

    manager = HeatingSystemManager(config)
    readings = _build_meter_readings()
    consumption_calc = ConsumptionCalculator(readings)
    cost_calc = CostCalculator(config.costs)
    runtime_calc = RuntimeCalculator()

    print("\n══════════════════════════════════════════════════")
    print("   hc_heat – Einmaliger Datenabruf")
    print("══════════════════════════════════════════════════")

    # Snapshot laden (Gaszähler immer holen im --once Modus)
    snapshot = manager.load_snapshot(force_gas=True)
    b = snapshot.boiler
    s = snapshot.system
    hc = snapshot.heating
    gas = snapshot.gas
    dhw = b.dhw
    dis = b.disinfection

    # Berechnungen
    state = runtime_calc.update(b)
    consumption = consumption_calc.calculate(b, gas, runtime_calc.disinfection_ratio())
    costs = cost_calc.calculate(consumption)

    _print_section("SYSTEM")
    _print_kv("Zeitstempel", snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    _print_kv("Betriebsmodus", state.mode.value)
    _print_kv("Außentemperatur", s.outdoor_temp, "°C")
    _print_kv("Heizung aktiv", s.heating_active)
    _print_kv("Heizung aus", s.heating_off)
    _print_kv("Warmwasser aktiv", s.tapwater_active)
    _print_kv("Heizkurve an", s.curve_on)
    _print_kv("Sommertemperatur", s.summer_temp, "°C")
    _print_kv("Frostschutz", s.frost_mode)
    _print_kv("Frosttemperatur", s.frost_temp, "°C")

    _print_section("BOILER / KESSEL")
    _print_kv("Vorlauftemperatur", b.flow_temp, "°C")
    _print_kv("Vorlauf Soll", b.flow_set_temp, "°C")
    _print_kv("Brenner aktiv", b.burner_active)
    _print_kv("Brenner aktiv 2", b.burner_active2)
    _print_kv("Heizung aktiviert", b.heating_enabled)
    _print_kv("Brennerleistung", b.burner_power_percent, "%")
    _print_kv("Brennerleistung Soll", b.burner_power_set, "%")
    _print_kv("Flammenstrom", b.flame_current, "µA")
    _print_kv("Nennleistung", b.nominal_power_kw, "kW")
    _print_kv("Aktuelle Leistung", b.current_power_kw(), "kW")

    _print_section("PUMPE")
    _print_kv("Pumpe aktiv", b.pump_active)
    _print_kv("Pumpe Modulation", b.pump_modulation, "%")
    _print_kv("Pumpe Modus", b.pump_mode)
    _print_kv("Pumpe Min", b.pump_min, "%")
    _print_kv("Pumpe Max", b.pump_max, "%")

    _print_section("HEIZKREIS")
    _print_kv("Vorlauf", hc.flow_temp, "°C")
    _print_kv("Rücklauf", hc.return_temp, "°C")
    _print_kv("Vorlauf Soll", hc.set_flow_temp, "°C")
    _print_kv("Pumpe aktiv", hc.pump_active)
    _print_kv("Modus", hc.mode)

    _print_section("WARMWASSER (DHW)")
    if dhw:
        _print_kv("Temperatur", dhw.curtemp, "°C")
        _print_kv("Temperatur 2", dhw.curtemp2, "°C")
        _print_kv("Solltemperatur", dhw.settemp, "°C")
        _print_kv("Offset", dhw.flowtempoffset, "°C")
        _print_kv("Komfort", dhw.comfort)
        _print_kv("Speichertyp", dhw.storage_type)
        _print_kv("Aktiviert", dhw.activated)
        _print_kv("Aktiv", dhw.active)
        _print_kv("Laden", dhw.charging)
        _print_kv("Nachladen", dhw.recharging)
        _print_kv("Temp OK", dhw.tempok)
        _print_kv("3-Wege-Ventil", dhw.threeway_valve)
        _print_kv("Ladepumpe", dhw.chargepump)
        _print_kv("Zirkulation", dhw.circpump)
        _print_kv("Starts", dhw.starts)
        _print_kv("Laufzeit", dhw.workm, "min")
        _print_kv("Energie", dhw.nrg, "kWh")
    else:
        print("  (keine Daten)")

    _print_section("DESINFEKTION")
    if dis:
        _print_kv("Aktiv", dis.active)
        _print_kv("Desinfektionstemperatur", dis.disinfection_temp, "°C")
        _print_kv("Aktuelle Temperatur", dis.curtemp, "°C")
    else:
        print("  (keine Daten)")

    _print_section("GASZÄHLER")
    if gas:
        _print_kv("Zählerstand (Display)", gas.display_m3, "m³")
        _print_kv("Verbrauch seit Install.", gas.total_m3, "m³")
        _print_kv("Zeitstempel", gas.timestamp)
        _print_kv("Periode Verbrauch", f"{consumption.period_gas_m3:.3f}", "m³")
    else:
        _print_kv("Status", "nicht abgefragt (Brenner aus)")

    _print_section("LAUFZEITEN")
    _print_kv("Brenner Starts", consumption.burner_starts)
    _print_kv("Brenner Laufzeit", consumption.burner_runtime_min, "min")
    _print_kv("Heizung Starts", consumption.heating_starts)
    _print_kv("Heizung Laufzeit", consumption.heating_runtime_min, "min")
    _print_kv("DHW Laufzeit (berechnet)", consumption.dhw_runtime_calculated_min, "min")
    _print_kv("DHW Starts (berechnet)", consumption.dhw_starts_calculated)
    _print_kv("Uptime", b.uptime_sec, "sec")

    _print_section("ENERGIE (kumulativ seit Installation)")
    _print_kv("Gesamt", consumption.energy_total_kwh, "kWh")
    _print_kv("Heizung", consumption.energy_heat_kwh, "kWh")
    _print_kv("Warmwasser", consumption.energy_dhw_kwh, "kWh")

    _print_section(f"ENERGIE (Periode {costs.energy_period})")
    _print_kv("Gesamt", f"{consumption.period_energy_total_kwh:.2f}", "kWh")
    _print_kv("Heizung", f"{consumption.period_energy_heat_kwh:.2f}", "kWh")
    _print_kv("Warmwasser", f"{consumption.period_energy_dhw_kwh:.2f}", "kWh")

    _print_section("KOSTEN")
    _print_kv("Gaspreis Zeitraum", costs.gas_period)
    _print_kv("Gaspreis", f"{config.costs.gas_price_per_kwh:.4f}", "€/kWh")
    _print_kv("Gaspreis (berechnet)", f"{config.costs.gas_price_per_m3:.3f}", "€/m³")
    print()
    _print_kv("Gas Periode (m³)", f"{costs.gas_total_eur:.2f}", costs.currency)
    _print_kv(
        "Gas Periode Gesamt (kWh)", f"{costs.energy_total_eur:.2f}", costs.currency
    )
    _print_kv("  davon Heizung", f"{costs.energy_heat_eur:.2f}", costs.currency)
    _print_kv("  davon Warmwasser", f"{costs.energy_dhw_eur:.2f}", costs.currency)

    _print_section("FEHLER / SERVICE")
    _print_kv("Letzter Fehlercode", b.lastcode)
    _print_kv("Servicecode", b.service_code)
    _print_kv("Servicecode Nr.", b.service_code_number)
    _print_kv("Wartungsmeldung", b.maintenance_message)
    _print_kv("Wartungsdatum", b.maintenance_date)

    print(f"\n{'══════════════════════════════════════════════════'}")
    print("  Fertig.")
    print()


def main() -> None:
    global _running

    # --once Modus
    if "--once" in sys.argv:
        run_once()
        return

    # Konfiguration laden
    config = load_config()

    # Logging einrichten
    setup_logging(config.log)

    # Simulate-Modus: nur Dashboard mit vorhandenen DB-Daten
    logger.info("APP_MODE = '%s'", config.app.app_mode)

    controller = HeatingController(config, running_flag=lambda: _running)

    if config.app.app_mode == "simulate":
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        controller.run_simulate()
    else:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        controller.run()


if __name__ == "__main__":
    main()
