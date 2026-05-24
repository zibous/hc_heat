"""Home Assistant Webhook-Events.

Sendet Events bei Zustandsänderungen:
- Neuer Fehler (Kessel oder Thermostat)
- Betriebsmodus geändert
- System OK wiederhergestellt
- Temperaturwarnung: dhw.curtemp < (flowtempoffset - 5)
"""

import logging
from typing import Optional

import requests

from config.app_config import HASettings

logger = logging.getLogger("hc_haco2.webhook")


class WebhookSender:
    """Sendet Events an Home Assistant per Webhook."""

    def __init__(self, settings: HASettings):
        self.settings = settings
        self._last_mode: Optional[str] = None
        self._last_error_boiler: Optional[str] = None
        self._last_error_thermostat: Optional[str] = None
        self._temp_warning_sent = False
        self._initialized = False
        # Endpoint-Status Tracking
        self._endpoint_status: dict[str, bool] = {
            "boiler": True,
            "thermostat": True,
            "gasmeter": True,
        }

    @property
    def enabled(self) -> bool:
        return self.settings.webhook_enabled

    def _send(self, event_type: str, data: dict) -> bool:
        """Sendet ein Event an HA."""
        if not self.enabled:
            return False
        url = f"{self.settings.webhook_url}/api/webhook/{self.settings.webhook_id}"
        payload = {"event": event_type, **data}
        try:
            r = requests.post(url, json=payload, timeout=5)
            logger.info("Webhook %s -> %d", event_type, r.status_code)
            return r.status_code == 200
        except Exception as e:
            logger.warning("Webhook fehlgeschlagen: %s", e)
            return False

    def check_and_send(
        self,
        mode: str,
        error_boiler: Optional[str],
        error_thermostat: Optional[str],
        dhw_curtemp: Optional[float],
        dhw_flowtempoffset: Optional[float],
    ) -> None:
        """Prüft auf Änderungen und sendet Events."""
        if not self.enabled:
            return

        # Erster Aufruf: Werte merken, keine Webhooks senden
        if not self._initialized:
            self._initialized = True
            self._last_mode = mode
            self._last_error_boiler = error_boiler
            self._last_error_thermostat = error_thermostat
            return

        # Betriebsmodus geändert
        if self._last_mode is not None and mode != self._last_mode:
            self._send(
                "mode_changed",
                {
                    "old_mode": self._last_mode,
                    "new_mode": mode,
                },
            )
        self._last_mode = mode

        # Neuer Kessel-Fehler
        # TODO: Fehler-Tracking ist doppelt implementiert (hier + ErrorLog in calc/error_log.py).
        #       Besser: ErrorLog als einzige Quelle, WebhookSender nur bei ErrorLog-Events senden.
        #       Siehe auch: _initialized Flag als Workaround für Startup-Spam.
        if error_boiler and error_boiler != self._last_error_boiler:
            self._send("error_boiler", {"code": error_boiler})
        self._last_error_boiler = error_boiler

        # Neuer Thermostat-Fehler
        if error_thermostat and error_thermostat != self._last_error_thermostat:
            self._send("error_thermostat", {"code": error_thermostat})
        self._last_error_thermostat = error_thermostat

        # Temperaturwarnung: dhw.curtemp < (flowtempoffset - 5)
        if (
            dhw_curtemp is not None
            and dhw_flowtempoffset is not None
            and dhw_curtemp < (dhw_flowtempoffset - 5)
        ):
            if not self._temp_warning_sent:
                self._send(
                    "temp_warning",
                    {
                        "dhw_curtemp": dhw_curtemp,
                        "threshold": dhw_flowtempoffset - 5,
                    },
                )
                self._temp_warning_sent = True
        else:
            if self._temp_warning_sent:
                self._send("system_ok", {"message": "Temperatur wieder normal"})
            self._temp_warning_sent = False

    def check_endpoint_status(
        self,
        boiler_ok: bool,
        thermostat_ok: bool,
        gasmeter_ok: bool,
    ) -> None:
        """Prüft Erreichbarkeit der Endpunkte und sendet Webhook bei Statuswechsel."""
        if not self.enabled:
            return

        endpoints = {
            "boiler": boiler_ok,
            "thermostat": thermostat_ok,
            "gasmeter": gasmeter_ok,
        }

        for name, is_ok in endpoints.items():
            was_ok = self._endpoint_status.get(name, True)
            if was_ok and not is_ok:
                # War online, jetzt offline
                self._send("endpoint_offline", {"endpoint": name})
            elif not was_ok and is_ok:
                # War offline, jetzt wieder online
                self._send("endpoint_online", {"endpoint": name})
            self._endpoint_status[name] = is_ok
