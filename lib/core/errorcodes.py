"""Fehlercode-Übersetzung für Buderus Heizungen.

Lädt Fehlercodes aus config/lang/errorcodes_{sprache}.yaml.
"""

import logging
import re
from datetime import datetime
from typing import Optional

import yaml

from config.app_config import BASE_DIR

logger = logging.getLogger("hc_haco2.errorcodes")

_codes: Optional[dict] = None
_PAREN_RE = re.compile(r"([0-9A-Za-z]+\(\d+\))")
_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})")


def _load_codes(language: str = "de") -> dict:
    """Lädt Fehlercodes aus der Sprachdatei."""
    global _codes
    if _codes is not None:
        return _codes

    path = BASE_DIR / "config" / "lang" / f"errorcodes_{language}.yaml"
    if not path.exists():
        logger.warning("Fehlercodes nicht gefunden: %s", path)
        _codes = {}
        return _codes

    try:
        with open(path, encoding="utf-8") as f:
            _codes = yaml.safe_load(f) or {}
        logger.debug("Fehlercodes geladen: %d Einträge", len(_codes or {}))
    except Exception as e:
        logger.error("Fehler beim Laden der Fehlercodes: %s", e)
        _codes = {}

    return _codes or {}


def translate_buderus_code(full_code: str, language: str = "de") -> dict:
    """Übersetzt einen Buderus-Fehlercode in Klartext.

    Args:
        full_code: Rohcode z.B. "6L(229) 24.01.2026 17:42 (0 min)"
        language: Sprachcode (default "de")

    Returns:
        Dict mit "desc" (Beschreibung) und "datetime" (ISO-String)
    """
    result = {
        "desc": "Keine Meldung",
        "datetime": datetime.now().isoformat(timespec="seconds"),
    }

    if not full_code:
        return result

    codes = _load_codes(language)
    full_code = full_code.strip()

    # Code extrahieren: zuerst "6L(229)", dann Fallback "6L"
    match = _PAREN_RE.search(full_code)
    if match:
        code_with_sub = match.group(1)
        base_match = re.match(r"([0-9A-Za-z]+)", code_with_sub)
        code_base = base_match.group(1) if base_match else code_with_sub
        # Zuerst spezifischen Untercode suchen, dann Basiscode
        desc = codes.get(code_with_sub) or codes.get(code_base)
    else:
        code_base = re.match(r"([0-9A-Za-z]+)", full_code)
        code_key = code_base.group(1) if code_base else full_code
        desc = codes.get(code_key)

    if desc:
        result["desc"] = desc
    else:
        result["desc"] = f"Unbekannter Code: {full_code[:20]}"

    # Datum extrahieren: "24.01.2026 17:42" → ISO
    date_match = _DATE_RE.search(full_code)
    if date_match:
        d_parts = date_match.group(1).split(".")
        if len(d_parts) == 3:
            iso = (
                f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}T{date_match.group(2)}:00+00:00"
            )
            result["datetime"] = iso

    return result
