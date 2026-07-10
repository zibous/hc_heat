"""Laufzeitberechnung nach Betriebsart."""

import logging
from datetime import datetime
from typing import Optional

from ..models.operation_state import OperationMode, OperationState
from ..models.boiler import Boiler

logger = logging.getLogger(" hc_heat.calc.runtime")


class RuntimeCalculator:
    """Berechnet Betriebszustände und Laufzeiten.

    Trackt kumulative Laufzeit pro Betriebsart seit App-Start.
    Damit kann der Desinfektions-Anteil an der DHW-Energie
    geschätzt werden.
    """

    def __init__(self) -> None:
        self._current_state: Optional[OperationState] = None
        self._history: list[OperationState] = []
        self._last_update: Optional[datetime] = None
        # Kumulative Sekunden pro Modus (seit App-Start)
        self._cumulative_sec: dict[OperationMode, float] = {
            OperationMode.STANDBY: 0.0,
            OperationMode.HEATING: 0.0,
            OperationMode.DHW: 0.0,
            OperationMode.DISINFECTION: 0.0,
        }

    def determine_mode(self, boiler: Boiler) -> OperationMode:
        """Bestimmt den aktuellen Betriebsmodus aus Boiler-Daten.

        Prioritäten (strikt):
        1. Desinfektion: dhw.disinfecting == true
           → Legionellenprogramm aktiv, höchste Priorität
        2. Warmwasser:   tapwater_active == true AND NOT disinfecting
           → 3-Wege-Ventil auf WW, Speicherladung aktiv
        3. Heizung:      heating_active == true AND NOT tapwater AND NOT disinfecting
           → Heizbetrieb, Vorlauftemperatur nach Heizkurve
        4. Standby:      alles andere
           → Keine Anforderung, nur Pumpennachlauf/Bereitschaft
        """
        is_disinfecting = bool(boiler.disinfection and boiler.disinfection.active)
        is_tapwater = bool(boiler.tapwater_active)
        is_heating = bool(boiler.heating_active)

        # 1. Desinfektion — höchste Priorität
        if is_disinfecting:
            return OperationMode.DISINFECTION

        # 2. Warmwasser — 3-Wege-Ventil auf WW
        if is_tapwater:
            return OperationMode.DHW

        # 3. Heizung — nur wenn kein WW und keine Desinfektion
        if is_heating:
            return OperationMode.HEATING

        # 4. Standby
        return OperationMode.STANDBY

    def update(self, boiler: Boiler) -> OperationState:
        """Aktualisiert den Betriebszustand und kumulative Zeiten."""
        now = datetime.now().astimezone()
        new_mode = self.determine_mode(boiler)

        # Kumulative Zeit zum aktuellen Modus addieren
        if self._last_update and self._current_state:
            delta = (now - self._last_update).total_seconds()
            self._cumulative_sec[self._current_state.mode] += delta
        self._last_update = now

        if self._current_state is None:
            self._current_state = OperationState(mode=new_mode, start=now)
        elif self._current_state.mode != new_mode:
            self._current_state.end = now
            self._history.append(self._current_state)
            logger.info(
                "Betriebswechsel: %s -> %s",
                self._current_state.mode.value,
                new_mode.value,
            )
            self._current_state = OperationState(mode=new_mode, start=now)

        return self._current_state

    @property
    def current_mode(self) -> Optional[OperationMode]:
        return self._current_state.mode if self._current_state else None

    @property
    def history(self) -> list[OperationState]:
        return list(self._history)

    def cumulative_seconds(self, mode: OperationMode) -> float:
        """Kumulative Sekunden einer Betriebsart seit App-Start."""
        return self._cumulative_sec.get(mode, 0.0)

    def cumulative_minutes(self, mode: OperationMode) -> int:
        """Kumulative Minuten einer Betriebsart seit App-Start."""
        return int(self._cumulative_sec.get(mode, 0.0) / 60)

    def disinfection_ratio(self) -> float:
        """Anteil Desinfektion an DHW+Desinfektion (0.0 - 1.0).

        Wird verwendet um DHW-Energie anteilig aufzuteilen.
        """
        dhw_sec = self._cumulative_sec[OperationMode.DHW]
        dis_sec = self._cumulative_sec[OperationMode.DISINFECTION]
        total = dhw_sec + dis_sec
        if total <= 0:
            return 0.0
        return dis_sec / total

    def total_runtime_hours(self, mode: OperationMode) -> float:
        """Gesamtlaufzeit einer Betriebsart in Stunden (aus History)."""
        total = sum(s.duration_seconds for s in self._history if s.mode == mode)
        return total / 3600.0

    def last_cycles(self) -> dict[str, dict]:
        """Letzter abgeschlossener Zyklus pro Betriebsart.

        Returns:
            Dict mit mode -> {start, end, duration_min}
        """
        result: dict[str, dict] = {}
        for state in reversed(self._history):
            key = state.mode.value
            if key == "standby" or key in result:
                continue
            dur = state.duration_seconds
            result[key] = {
                "start": state.start.isoformat(),
                "end": state.end.isoformat() if state.end else None,
                "duration_min": round(dur / 60, 1),
            }
            if len(result) >= 3:
                break
        return result
