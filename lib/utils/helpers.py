"""Hilfsfunktionen für Typkonvertierung und Datenextraktion."""

from typing import Optional


def parse_timestamp(value: object) -> Optional[str]:
    """Parst einen Timestamp-String und liefert ISO-Format zurück.

    Unterstützte Formate (in Prioritätsreihenfolge):
      - ISO: 2026-04-28T16:10:44 oder 2026-04-28T16:10:44.123456
      - ISO mit Leerzeichen: 2026-04-28 16:10:44
      - Deutsch: 28.04.2026 16:10 oder 28.04.2026 16:10:44
      - Timezone-Suffixe (CEST, CET, UTC, GMT) werden entfernt.
    """
    if value is None or not isinstance(value, str):
        return None

    clean = value.strip()

    # Timezone-Suffixe entfernen
    for tz in (" CEST", " CET", " UTC", " GMT"):
        if clean.endswith(tz):
            clean = clean[: -len(tz)]
            break

    # ISO-Format: 2026-04-28T16:10:44 oder mit Mikrosekunden
    if len(clean) >= 19 and clean[4] == "-" and clean[7] == "-":
        # Bereits ISO – nur validieren
        sep = clean[10] if len(clean) > 10 else ""
        if sep in ("T", " ", ""):
            return clean.replace(" ", "T") if " " in clean[:11] else clean

    # Deutsches Format: 28.04.2026 16:10[:44]
    if len(clean) >= 16 and clean[2] == "." and clean[5] == ".":
        parts = clean.split(" ", 1)
        if len(parts) == 2:
            date_parts = parts[0].split(".")
            if len(date_parts) == 3:
                iso = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}T{parts[1]}"
                return iso

    # Nicht erkannt – Originalwert zurückgeben
    return value


def safe_get(data: dict, *keys: str, default: object = None) -> object:
    """Sucht den ersten vorhandenen Key in einem dict (NICHT verschachtelt)."""
    if not isinstance(data, dict):
        return default
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def to_float(value: object, default: Optional[float] = None) -> Optional[float]:
    """Konvertiert zu float, gibt default bei Fehler zurück."""
    if value is None or value == "":
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return default


def to_int(value: object, default: Optional[int] = None) -> Optional[int]:
    """Konvertiert zu int, gibt default bei Fehler zurück."""
    if value is None or value == "":
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return default


def to_bool(value: object, default: Optional[bool] = None) -> Optional[bool]:
    """Bool-Konvertierung für EMS-ESP Werte ('an'/'aus', 'on'/'off', bool, int)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("an", "on", "true", "1"):
        return True
    if s in ("aus", "off", "false", "0"):
        return False
    return default
