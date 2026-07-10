"""HeatingSystemManager: Lädt alle Heizungsdaten über HTTP."""

import logging
import time
from typing import Optional
from datetime import datetime, timezone

import requests

from config.app_config import AppConfig
from ..models.system_data import SystemData
from ..models.boiler import Boiler
from ..models.heating_circuit import HeatingCircuit
from ..models.gas_meter import GasMeter
from ..models.thermostat import Thermostat
from ..models.heating_system import HeatingSystem
from ..models.heating_snapshot import HeatingSnapshot

logger = logging.getLogger(" hc_heat.manager")


class HeatingSystemManager:
    """Lädt Heizungsdaten über HTTP und baut Datenmodelle.

    Gaszähler wird nur abgefragt wenn der Brenner aktiv ist
    oder innerhalb der TTL nach Brenner-Stopp (schont ESPHome).
    """

    def __init__(self, config: AppConfig, timeout: int = 5):
        self.config = config
        self.boiler_url = config.heating.sensor_url
        self.system_info_url = config.heating.info_url
        self.thermostat_url = config.heating.thermostat_url
        self.gasmeter_url = config.gasmeter.sensor_url or None
        self.timeout = timeout

        # Gaszähler-Steuerung
        self._gas_ttl = config.app.gas_ttl
        self._last_burner_active_time: float = 0.0
        self._last_gas: Optional[GasMeter] = None

        # System-Info Cache (ändert sich fast nie)
        self._system_cache_ttl = config.heating.system_cache_ttl
        self._cached_system: Optional[SystemData] = None
        self._system_cache_time: float = 0.0

    def _get_json(self, url: str) -> dict:
        """HTTP GET mit Fehlerbehandlung."""
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.debug("GET %s -> %d bytes", url, len(response.content))
            return response.json()
        except requests.ConnectionError:
            logger.warning("Verbindung fehlgeschlagen: %s", url)
            return {}
        except requests.Timeout:
            logger.warning("Timeout bei: %s", url)
            return {}
        except Exception as e:
            logger.error("HTTP Fehler bei %s: %s", url, e)
            return {}

    def _should_fetch_gas(self, boiler: Boiler) -> bool:
        """Prüft ob der Gaszähler abgefragt werden soll.

        Abfrage nur wenn:
        - Brenner aktiv ist, ODER
        - Brenner vor weniger als gas_ttl Sekunden aktiv war (Nachlauf)
        """
        if not self.gasmeter_url:
            return False

        now = time.monotonic()

        if boiler.burner_active:
            self._last_burner_active_time = now
            return True

        # Nachlauf: noch innerhalb TTL nach letztem Brennerbetrieb
        elapsed = now - self._last_burner_active_time
        if self._last_burner_active_time > 0 and elapsed <= self._gas_ttl:
            logger.debug(
                "Gas-Nachlauf: %.0fs von %ds",
                elapsed,
                self._gas_ttl,
            )
            return True

        return False

    def load_gasmeter(self, boiler: Optional[Boiler] = None) -> Optional[GasMeter]:
        """Lädt Gaszähler-Daten – nur wenn Brenner aktiv oder Nachlauf.

        Args:
            boiler: Aktuelle Boiler-Daten für Brenner-Check.
                    Wenn None, wird immer abgefragt (für Einzelabruf).
        """
        if not self.gasmeter_url:
            return None

        # Wenn Boiler übergeben: prüfe ob Abruf nötig
        if boiler is not None and not self._should_fetch_gas(boiler):
            logger.debug("Gaszähler übersprungen (Brenner aus, TTL abgelaufen)")
            return self._last_gas

        data = self._get_json(self.gasmeter_url)
        cfg = {
            "idx_display": self.config.gasmeter.idx_display,
            "idx_total": self.config.gasmeter.idx_total,
            "idx_ts": self.config.gasmeter.idx_ts,
        }
        self._last_gas = GasMeter.from_api(data, cfg)
        return self._last_gas

    def load_thermostat(self) -> Optional[Thermostat]:
        """Lädt Thermostat-Daten vom EMS-ESP."""
        data = self._get_json(self.thermostat_url)
        if not data:
            return None
        return Thermostat.from_api(data)

    def _load_system_cached(self, boiler_data: dict) -> SystemData:
        """Lädt System-Daten mit Cache (ändert sich fast nie)."""
        now = time.monotonic()
        if (
            self._cached_system is not None
            and (now - self._system_cache_time) < self._system_cache_ttl
        ):
            return self._cached_system

        self._cached_system = SystemData.from_api(boiler_data)
        self._system_cache_time = now
        logger.debug("System-Info aktualisiert (TTL: %ds)", self._system_cache_ttl)
        return self._cached_system

    def load_snapshot(self, force_gas: bool = False) -> HeatingSnapshot:
        """Erstellt einen kompletten Snapshot aller Daten.

        Boiler-Endpoint wird nur einmal abgefragt.
        Gaszähler nur wenn Brenner aktiv, Nachlauf, oder force_gas=True.
        """
        boiler_data = self._get_json(self.boiler_url)
        logger.debug("Boiler-Daten geladen: %d Keys", len(boiler_data))

        system = self._load_system_cached(boiler_data)
        boiler = Boiler.from_api(boiler_data)
        heating = HeatingCircuit.from_api(boiler_data)
        gas = self.load_gasmeter(None if force_gas else boiler)
        thermostat = self.load_thermostat()

        return HeatingSnapshot(
            timestamp=datetime.now().astimezone(),
            system=system,
            boiler=boiler,
            heating=heating,
            gas=gas,
            thermostat=thermostat,
        )

    def load_system(self) -> HeatingSystem:
        """Lädt das komplette Heizungssystem."""
        boiler_data = self._get_json(self.boiler_url)
        boiler = Boiler.from_api(boiler_data)

        return HeatingSystem(
            system=self._load_system_cached(boiler_data),
            boiler=boiler,
            heating=HeatingCircuit.from_api(boiler_data),
            gas=self.load_gasmeter(boiler),
            thermostat=self.load_thermostat(),
        )
