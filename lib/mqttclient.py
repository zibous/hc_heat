"""MQTT Client – optional, mit automatischem Reconnect.

Verbindet sich zu einem bestehenden MQTT Broker.
Wenn der Broker nicht erreichbar ist, läuft die App weiter
und versucht regelmäßig erneut zu verbinden.
"""

import json
import logging
import time
from typing import Optional

from config.app_config import MQTTSettings

logger = logging.getLogger("hc_haco2.mqtt")

try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.info("paho-mqtt nicht installiert – MQTT deaktiviert")


class MQTTClient:
    """MQTT Publisher mit automatischem Reconnect.

    paho.mqtt reconnected automatisch im Hintergrund (loop_start).
    Wenn der Broker beim Start nicht da ist, wird alle 5 Minuten
    ein neuer Verbindungsversuch gemacht.
    """

    def __init__(self, settings: MQTTSettings):
        self.settings = settings
        self._client: Optional[object] = None
        self._connected = False
        self._last_payload: Optional[str] = None
        self._last_connect_attempt: float = 0
        self._reconnect_interval = 300  # 5 Minuten
        self._first_attempt: float = 0
        self._give_up_after = 1800  # 30 Minuten, dann aufgeben
        self._gave_up = False

    @property
    def enabled(self) -> bool:
        return MQTT_AVAILABLE and self.settings.enabled and not self._gave_up

    def connect(self) -> bool:
        """Verbindet zum MQTT Broker."""
        if not self.enabled:
            return False

        self._last_connect_attempt = time.monotonic()

        try:
            if not self._client:
                self._client = mqtt.Client(
                    client_id=self.settings.client_id,
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
                )
                if self.settings.user:
                    self._client.username_pw_set(
                        self.settings.user, self.settings.password
                    )
                self._client.on_connect = self._on_connect
                self._client.on_disconnect = self._on_disconnect
                # Auto-Reconnect durch paho
                self._client.reconnect_delay_set(min_delay=5, max_delay=120)

            logger.info(
                "MQTT verbinde zu %s:%d ...", self.settings.host, self.settings.port
            )
            self._client.connect_async(
                self.settings.host,
                self.settings.port,
                self.settings.keepalive,
            )
            self._client.loop_start()
            # Kurz warten
            time.sleep(2)
            return self._connected
        except Exception as e:
            logger.warning(
                "MQTT Verbindung fehlgeschlagen: %s (wird später erneut versucht)", e
            )
            self._connected = False
            return False

    def _on_connect(
        self,
        client: object,
        userdata: object,
        flags: object,
        rc: object,
        properties: object = None,
    ) -> None:
        logger.info("MQTT verbunden (rc=%s)", rc)
        self._connected = True

    def _on_disconnect(
        self,
        client: object,
        userdata: object,
        flags: object,
        rc: object,
        properties: object = None,
    ) -> None:
        if rc != 0:
            logger.warning("MQTT getrennt (rc=%s) – paho reconnected automatisch", rc)
        self._connected = False

    def publish(self, topic: str, payload: dict) -> bool:
        """Publiziert JSON-Daten. Versucht Reconnect wenn nötig."""
        if not self.enabled:
            return False

        if not payload:
            return False

        json_str = json.dumps(payload, ensure_ascii=False)

        # Duplikat-Check
        if json_str == self._last_payload:
            return False

        # Noch nicht verbunden? Periodisch neuen Versuch starten
        if not self._connected:
            if self._gave_up:
                return False
            elapsed = time.monotonic() - self._last_connect_attempt
            if elapsed >= self._reconnect_interval:
                # Prüfe ob Timeout erreicht
                if self._first_attempt == 0:
                    self._first_attempt = time.monotonic()
                total_elapsed = time.monotonic() - self._first_attempt
                if total_elapsed >= self._give_up_after:
                    logger.error(
                        "MQTT: %d min ohne Verbindung – MQTT deaktiviert",
                        int(total_elapsed / 60),
                    )
                    self._gave_up = True
                    return False
                logger.info("MQTT Reconnect-Versuch...")
                self.connect()
            if not self._connected:
                return False

        # Verbunden → Timer zurücksetzen
        self._first_attempt = 0

        if not self._client:
            return False

        try:
            result = self._client.publish(topic, json_str, qos=1)
            if result.rc == 0:
                self._last_payload = json_str
                logger.debug("MQTT publish -> %s", topic)
                return True
            logger.warning("MQTT publish fehlgeschlagen: rc=%d", result.rc)
            return False
        except Exception as e:
            logger.error("MQTT publish Fehler: %s", e)
            return False

    def disconnect(self) -> None:
        """Trennt die MQTT Verbindung."""
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
                logger.info("MQTT getrennt")
            except Exception:
                pass
            finally:
                self._connected = False
