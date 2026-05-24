"""Feld-Mapping: Übersetzt API-Keys in interne Feldnamen.

Ermöglicht Anpassung an verschiedene EMS-ESP Firmware-Versionen
ohne Code-Änderungen – nur field_mappings.yaml anpassen.

Unterstützt zwei JSON-Formate:
  1. Boiler-API:     {"curflowtemp": 38.6, ...}         (flache Keys)
  2. Thermostat-API:  {"HK1 Betriebsart (mode)": "auto"} (Langname mit Key in Klammern)
"""

import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from config.app_config import BASE_DIR

logger = logging.getLogger("hc_haco2.mapper")

# Globaler Cache
_mappings: Optional[dict] = None

# Regex: extrahiert "api_key" aus "Beschreibung (api_key)"
_PAREN_RE = re.compile(r"\((\w+)\)\s*$")


def load_mappings(config_dir: Optional[Path] = None) -> dict:
    """Lädt Feld-Mappings aus field_mappings.yaml."""
    global _mappings
    if _mappings is not None:
        return _mappings

    config_dir = config_dir or BASE_DIR / "config"
    path = config_dir / "field_mappings.yaml"

    if not path.exists():
        logger.debug("field_mappings.yaml nicht gefunden – verwende Defaults")
        _mappings = {}
        return _mappings

    try:
        with open(path, encoding="utf-8") as f:
            _mappings = yaml.safe_load(f) or {}
        logger.debug("Feld-Mappings geladen: %s", list((_mappings or {}).keys()))
    except Exception as e:
        logger.error("Fehler beim Laden von field_mappings.yaml: %s", e)
        _mappings = {}

    return _mappings or {}


def normalize_keys(data: dict) -> dict:
    """Normalisiert Thermostat-API Keys.

    Wandelt "HK1 Betriebsart (mode)" → "mode" um.
    Flache Keys (ohne Klammern) bleiben unverändert.
    Gibt ein neues Dict mit normalisierten Keys zurück.
    """
    if not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        m = _PAREN_RE.search(key)
        if m:
            short_key = m.group(1)
            result[short_key] = value
        else:
            result[key] = value
    return result


def mapped_get(
    data: dict,
    field_name: str,
    section: str,
    default: Any = None,
) -> Any:
    """Holt einen Wert aus data anhand des Feld-Mappings.

    Sucht zuerst in den normalisierten Keys, dann in den Original-Keys.
    """
    mappings = load_mappings()
    section_map = mappings.get(section, {})
    api_keys = section_map.get(field_name)

    if not api_keys:
        return default

    if isinstance(api_keys, str):
        api_keys = [api_keys]

    for key in api_keys:
        if key in data and data[key] is not None:
            return data[key]

    return default
