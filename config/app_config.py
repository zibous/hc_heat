"""Zentrale Konfiguration – lädt alle Einstellungen aus .env und YAML."""

import os
import logging
from pathlib import Path
from datetime import date
from dataclasses import dataclass, field
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Projektverzeichnis (hc_heat2/)
BASE_DIR = Path(__file__).resolve().parent.parent


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip().strip('"').strip("'")


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes", "an")


@dataclass
class AppSettings:
    """Allgemeine Anwendungseinstellungen."""

    language: str = ""
    dashboard_port: int = 0
    dashboard_base_path: str = ""
    interval: int = 60
    fast_interval: int = 10
    slow_interval: int = 300
    gas_ttl: int = 30
    save_snapshots: bool = False
    save_history: bool = True
    history_dir: str = "./data/history"
    history_keep_weeks: int = 8
    app_mode: str = "production"


@dataclass
class LogSettings:
    """Logging-Konfiguration."""

    level: str = "INFO"
    mode: str = "console"
    file: str = ""
    max_bytes: int = 1_000_000
    backup_count: int = 3
    enabled: bool = True
    flow_tracer: bool = False


@dataclass
class HeatingDevice:
    """Geräteinformationen Heizung."""

    device_id: str = ""
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    software: str = ""
    installed: str = ""
    sensor_url: str = ""
    thermostat_url: str = ""
    info_url: str = ""
    system_cache_ttl: int = 3600  # System-Info nur alle 60 Min abrufen


@dataclass
class GasMeterDevice:
    """Geräteinformationen Gaszähler."""

    sensor_url: str = ""
    idx_display: int = 0
    idx_total: int = 1
    idx_ts: int = 2


@dataclass
class MQTTSettings:
    """MQTT Broker Konfiguration."""

    host: str = ""
    port: int = 1883
    user: str = ""
    password: str = ""
    keepalive: int = 60
    client_id: str = ""

    # Topics
    topic_status: str = ""
    topic_boiler: str = ""
    topic_dhw: str = ""
    topic_heating: str = ""
    topic_energy: str = ""
    topic_costs: str = ""
    topic_gas: str = ""
    topic_raw: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.host)


@dataclass
class HASettings:
    """Home Assistant Konfiguration."""

    discovery: bool = False
    prefix: str = ""
    discovery_prefix: str = "homeassistant"
    data_dir: str = ""
    webhook_url: str = ""
    webhook_id: str = ""

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.webhook_url and self.webhook_id)


@dataclass
class CostSettings:
    """Kosten-Konfiguration aus costs.yaml – zeitraumabhängig.

    Gaspreise: Abrechnungszeitraum 01.09. bis 31.08. Folgejahr
    Energiepreise: pro Kalenderjahr
    """

    gas_price_per_kwh: float = 0.0
    energy_price_per_kwh: float = 0.0
    gas_kwh_per_m3: float = 10.19
    currency: str = "EUR"
    gas_period: str = ""  # z.B. "2025-09-01 – 2026-08-31"
    energy_period: str = ""  # z.B. "2026"

    @property
    def gas_price_per_m3(self) -> float:
        """Gaspreis pro m³ (berechnet aus kWh-Preis × Brennwert)."""
        return self.gas_price_per_kwh * self.gas_kwh_per_m3


@dataclass
class AppConfig:
    """Gesamtkonfiguration der Anwendung."""

    app: AppSettings = field(default_factory=AppSettings)
    log: LogSettings = field(default_factory=LogSettings)
    heating: HeatingDevice = field(default_factory=HeatingDevice)
    gasmeter: GasMeterDevice = field(default_factory=GasMeterDevice)
    mqtt: MQTTSettings = field(default_factory=MQTTSettings)
    ha: HASettings = field(default_factory=HASettings)
    costs: CostSettings = field(default_factory=CostSettings)


def load_costs(
    config_dir: Optional[Path] = None, ref_date: Optional[date] = None
) -> CostSettings:
    """Lädt Kosten aus costs.yaml für das aktuelle Datum.

    Gas:    Zeitraum 01.09. – 31.08. (periods mit from/to)
    Energie: Kalenderjahr (periods mit year)
    """
    config_dir = config_dir or BASE_DIR / "config"
    costs_file = config_dir / "costs.yaml"
    if not costs_file.exists():
        logger.warning("costs.yaml nicht gefunden: %s", costs_file)
        return CostSettings()

    today = ref_date or date.today()

    try:
        with open(costs_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Fehler beim Laden von costs.yaml: %s", e)
        return CostSettings()

    # --- Gas: passenden Zeitraum finden ---
    gas_cfg = data.get("gas", {})
    gas_kwh_per_m3 = float(gas_cfg.get("kwh_per_m3", 10.19))
    currency = gas_cfg.get("currency", "EUR")
    gas_price_kwh = 0.0
    gas_period = ""

    for p in gas_cfg.get("periods", []):
        p_from = date.fromisoformat(str(p["from"]))
        p_to = date.fromisoformat(str(p["to"]))
        if p_from <= today <= p_to:
            gas_price_kwh = float(p.get("price_per_kwh", 0))
            gas_period = f"{p_from} – {p_to}"
            break

    if not gas_period:
        # Fallback: letzten Eintrag nehmen
        periods = gas_cfg.get("periods", [])
        if periods:
            p = periods[-1]
            gas_price_kwh = float(p.get("price_per_kwh", 0))
            gas_period = f"{p.get('from')} – {p.get('to')} (Fallback)"
            logger.warning("Kein Gaspreis für %s – verwende letzten Eintrag", today)

    # --- Energie: passendes Kalenderjahr finden ---
    energy_cfg = data.get("energy", {})
    energy_price_kwh = 0.0
    energy_period = ""

    for p in energy_cfg.get("periods", []):
        if int(p["year"]) == today.year:
            energy_price_kwh = float(p.get("price_per_kwh", 0))
            energy_period = str(p["year"])
            break

    if not energy_period:
        periods = energy_cfg.get("periods", [])
        if periods:
            p = periods[-1]
            energy_price_kwh = float(p.get("price_per_kwh", 0))
            energy_period = f"{p['year']} (Fallback)"
            logger.warning(
                "Kein Energiepreis für %d – verwende letzten Eintrag", today.year
            )

    logger.info(
        "Gaspreis: %.4f €/kWh (%.3f €/m³) (%s)",
        gas_price_kwh,
        gas_price_kwh * gas_kwh_per_m3,
        gas_period,
    )
    logger.info("Energiepreis: %.4f €/kWh (%s)", energy_price_kwh, energy_period)

    return CostSettings(
        gas_price_per_kwh=gas_price_kwh,
        energy_price_per_kwh=energy_price_kwh,
        gas_kwh_per_m3=gas_kwh_per_m3,
        currency=currency,
        gas_period=gas_period,
        energy_period=energy_period,
    )


def load_meter_readings(
    data_dir: Optional[Path] = None, ref_date: Optional[date] = None
) -> dict:
    """Lädt Zählerstände zu Periodenbeginn aus meter_readings.yaml.

    Returns:
        Dict mit Keys: nrg_total_start, nrg_heat_start, nrg_dhw_start,
        energy_year, gas_total_start, gas_period
    """
    data_dir = data_dir or BASE_DIR / "data"
    readings_file = data_dir / "meter_readings.yaml"
    today = ref_date or date.today()

    result = {
        "nrg_total_start": 0.0,
        "nrg_heat_start": 0.0,
        "nrg_dhw_start": 0.0,
        "energy_year": today.year,
        "gas_total_start": 0.0,
        "gas_period": "",
    }

    if not readings_file.exists():
        logger.warning("meter_readings.yaml nicht gefunden: %s", readings_file)
        return result

    try:
        with open(readings_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Fehler beim Laden von meter_readings.yaml: %s", e)
        return result

    # Gas-Periode finden (01.09. – 31.08.)
    for p in data.get("gas_periods", []):
        p_from = date.fromisoformat(str(p["from"]))
        p_to = date.fromisoformat(str(p["to"]))
        if p_from <= today <= p_to:
            result["gas_total_start"] = float(p.get("gas_total_m3", 0))
            result["gas_period"] = f"{p_from} – {p_to}"
            break

    # Energie-Periode finden (Kalenderjahr)
    for p in data.get("energy_periods", []):
        if int(p["year"]) == today.year:
            result["nrg_total_start"] = float(p.get("nrg_total_kwh", 0))
            result["nrg_heat_start"] = float(p.get("nrg_heat_kwh", 0))
            result["nrg_dhw_start"] = float(p.get("nrg_dhw_kwh", 0))
            result["energy_year"] = int(p["year"])
            break

    logger.info(
        "Zählerstände: Gas=%.1f m³ (%s), Energie=%.1f kWh (%d)",
        result["gas_total_start"],
        result["gas_period"],
        result["nrg_total_start"],
        result["energy_year"],
    )
    return result


def load_config() -> AppConfig:
    """Lädt die komplette Konfiguration aus .env und YAML-Dateien."""
    cfg = AppConfig(
        app=AppSettings(
            language=_env("LANGUAGE", "de"),
            dashboard_port=_env_int("DASHBOARD_PORT", 5028),
            dashboard_base_path=_env("DASHBOARD_BASE_PATH", "/dashboardheizung"),
            interval=_env_int("INTERVALL", 60),
            fast_interval=_env_int("FAST_INTERVAL", 10),
            slow_interval=_env_int("SLOW_INTERVAL", 300),
            gas_ttl=_env_int("GAS_TTL", 30),
            save_snapshots=_env_bool("SAVE_SNAPSHOTS", False),
            save_history=_env_bool("SAVE_HISTORY", True),
            history_dir=_env("HISTORY_DIR", "./data/history"),
            history_keep_weeks=_env_int("HISTORY_KEEP_WEEKS", 8),
            app_mode=_env("APP_MODE", "production"),
        ),
        log=LogSettings(
            level=_env("LOG_LEVEL", "INFO"),
            mode=_env("LOG_MODE", "console"),
            file=_env("LOG_FILE", "heizung.log"),
            max_bytes=_env_int("LOG_MAX_BYTES", 1_000_000),
            backup_count=_env_int("LOG_BACKUP_COUNT", 3),
            enabled=_env_bool("LOGGING_ON", True),
            flow_tracer=_env_bool("FLOW_TRACER", False),
        ),
        heating=HeatingDevice(
            device_id=_env("HEATING_ID", "LOGAMAX"),
            name=_env("HEATING_NAME", "Heizungsanlage 2021"),
            manufacturer=_env("HEATING_MANUFACTURER", "Buderus"),
            model=_env("HEATING_MODEL", "Buderus LOGAMAX PLUS GB172-14"),
            software=_env("HEATING_SOFTWARE", "2.0.0"),
            installed=_env("HEATING_INSTALLED", "2021-06-06 12:00:00"),
            sensor_url=_env(
                "HEATING_SENSOR",
                "http://ems-heizung.siebler.home/api/boiler",
            ),
            thermostat_url=_env(
                "HEATING_THERMOSTAT",
                "http://ems-heizung.siebler.home/api/thermostat",
            ),
            info_url=_env(
                "HEATING_INFO",
                "http://ems-heizung.siebler.home/api/system/info",
            ),
            system_cache_ttl=_env_int("SYSTEM_CACHE_TTL", 3600),
        ),
        gasmeter=GasMeterDevice(
            sensor_url=_env("GASMETER_SENSOR", ""),
            idx_display=_env_int("GASMETER_DISPLAY", 0),
            idx_total=_env_int("GASMETER_M3", 1),
            idx_ts=_env_int("GASMETER_TS", 2),
        ),
        mqtt=MQTTSettings(
            host=_env("MQTT_HOST", ""),
            port=_env_int("MQTT_PORT", 1883),
            user=_env("MQTT_USER", ""),
            password=_env("MQTT_PASS", ""),
            keepalive=_env_int("MQTT_KEEPALIVE", 60),
            client_id=_env("MQTT_CLIENTID", "heizungscontroller"),
            topic_status=_env("MQTT_TOPIC_STATUS", "logamax/status"),
            topic_boiler=_env("MQTT_TOPIC_BOILER", "logamax/boiler"),
            topic_dhw=_env("MQTT_TOPIC_DHW", "logamax/dhw"),
            topic_heating=_env("MQTT_TOPIC_HEATING", "logamax/heating"),
            topic_energy=_env("MQTT_TOPIC_ENERGY", "logamax/energy"),
            topic_costs=_env("MQTT_TOPIC_COSTS", "logamax/costs"),
            topic_gas=_env("MQTT_TOPIC_GAS", "logamax/gas"),
            topic_raw=_env("MQTT_TOPIC_RAW", "logamax/rawdata"),
        ),
        ha=HASettings(
            discovery=_env_bool("HA_DISCOVERY", False),
            prefix=_env("HA_PREFIX", "logamax"),
            discovery_prefix=_env("HA_DISCOVERY_PREFIX", "homeassistant"),
            data_dir=_env("HA_DATADIR", "./data/homeassistant/"),
            webhook_url=_env("HA_WEBHOOK_URL", ""),
            webhook_id=_env("HA_WEBHOOK_ID", ""),
        ),
        costs=load_costs(),
    )
    return cfg
