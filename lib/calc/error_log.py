"""Fehler-Tracking für die Heizungsanlage mit Klartext-Übersetzung."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..core.errorcodes import translate_buderus_code

logger = logging.getLogger(" hc_heat.calc.error")


@dataclass
class ErrorEntry:
    """Ein Fehlereintrag mit Klartext-Beschreibung."""

    timestamp: datetime
    code: str  # Rohcode z.B. "6L(229) 24.01.2026 17:42 (0 min)"
    description: str  # Klartext z.B. "Keine Ionisation während Brennerbetrieb"
    error_date: str  # Datum aus dem Code z.B. "2026-01-24T17:42:00+00:00"
    source: str = ""  # "boiler" oder "thermostat"


class ErrorLog:
    """Verwaltet Fehlermeldungen der Heizung mit Klartext-Übersetzung."""

    def __init__(self) -> None:
        self._errors: list[ErrorEntry] = []
        self._last_codes: dict[str, str] = {}  # source -> letzter Code
        self._initialized: set[str] = set()  # sources die den ersten Code gesehen haben

    def check_error(
        self, lastcode: Optional[str], source: str = "boiler"
    ) -> Optional[ErrorEntry]:
        """Prüft ob ein neuer Fehler vorliegt.

        Args:
            lastcode: Rohcode aus der API
            source: "boiler" oder "thermostat"

        Returns:
            ErrorEntry wenn neuer Fehler, sonst None.
        """
        if not lastcode:
            return None

        # Duplikat-Check pro Quelle
        # TODO: ErrorLog sollte die einzige Fehler-Erkennung sein.
        #       WebhookSender.check_and_send() hat eigene Duplikat-Logik → redundant.
        #       Refactoring: ErrorLog meldet neue Fehler → Controller sendet Webhook.
        if lastcode == self._last_codes.get(source):
            return None

        self._last_codes[source] = lastcode

        # Erster Aufruf nach Start: Code merken, aber nicht als neuen Fehler melden
        if source not in self._initialized:
            self._initialized.add(source)
            logger.debug("Initialer %s-Code: %s (kein Webhook)", source, lastcode)
            return None

        # Klartext-Übersetzung
        translated = translate_buderus_code(lastcode)

        entry = ErrorEntry(
            timestamp=datetime.now().astimezone(),
            code=lastcode,
            description=translated["desc"],
            error_date=translated["datetime"],
            source=source,
        )
        self._errors.append(entry)
        logger.warning("Neuer %s-Fehler: %s → %s", source, lastcode, translated["desc"])
        return entry

    @property
    def last_error(self) -> Optional[ErrorEntry]:
        return self._errors[-1] if self._errors else None

    def last_error_by_source(self, source: str) -> Optional[ErrorEntry]:
        """Letzter Fehler einer bestimmten Quelle."""
        for e in reversed(self._errors):
            if e.source == source:
                return e
        return None

    @property
    def count(self) -> int:
        return len(self._errors)

    @property
    def errors(self) -> list[ErrorEntry]:
        return list(self._errors)
