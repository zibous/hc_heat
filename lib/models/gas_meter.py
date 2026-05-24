"""Gaszähler-Datenmodell für ESPHome Text-Sensor.

Format: "displayvalue|totalm3|timestamp"
  - displayvalue: Physischer Zählerstand (startet nicht bei 0)
  - totalm3:      Gesamtverbrauch seit ESP-Installation (startet bei 0)
  - timestamp:    Zeitstempel der letzten Messung
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..utils.helpers import to_float, parse_timestamp


@dataclass
class GasMeter:
    """Gaszähler-Daten vom ESPHome ESP32 Sensor."""

    display_m3: Optional[float] = None  # Physischer Zählerstand
    total_m3: Optional[float] = None  # Verbrauch seit ESP-Installation
    timestamp: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict, cfg: Optional[dict] = None) -> "GasMeter":
        """Erstellt GasMeter aus der ESPHome Text-Sensor Antwort.

        Format: {"value": "32380.797|3320.143|2026-04-28T16:10:44 CEST"}
        Indices konfigurierbar über cfg dict (aus .env).
        """
        if not data:
            return cls()

        cfg = cfg or {}
        idx_display = cfg.get("idx_display", 0)
        idx_total = cfg.get("idx_total", 1)
        idx_ts = cfg.get("idx_ts", 2)

        value = data.get("state") or data.get("value") or ""
        display = None
        total = None
        ts = None

        if isinstance(value, str) and "|" in value:
            parts = [p.strip() for p in value.split("|")]
            if idx_display < len(parts):
                display = to_float(parts[idx_display])
            if idx_total < len(parts):
                total = to_float(parts[idx_total])
            if idx_ts < len(parts):
                ts = parse_timestamp(parts[idx_ts])
        elif isinstance(value, dict):
            display = to_float(value.get("display") or value.get("value"))
            total = to_float(value.get("total") or value.get("m3"))
            ts = parse_timestamp(value.get("timestamp"))
        elif value:
            display = to_float(value)

        return cls(
            display_m3=display,
            total_m3=total,
            timestamp=ts,
            raw=data,
        )
