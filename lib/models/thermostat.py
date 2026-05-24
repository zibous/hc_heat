"""Thermostat-Datenmodell – Daten vom RC310 Regler (/api/thermostat)."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..utils.field_mapper import mapped_get, normalize_keys
from ..utils.helpers import to_float, to_bool, to_int

_S = "thermostat"
_HC = "thermostat_hc1"
_WW = "thermostat_wwk"


@dataclass
class ThermostatHC1:
    """Heizkreis 1 Daten vom Thermostat."""

    mode: Optional[str] = None  # auto, manuell
    modetype: Optional[str] = None  # Komfort, Eco
    seltemp: Optional[float] = None  # Gewählte Raumtemperatur
    comforttemp: Optional[float] = None  # Komforttemperatur
    ecotemp: Optional[float] = None  # Eco-Temperatur
    manualtemp: Optional[float] = None  # Manuelle Temperatur
    summertemp: Optional[float] = None  # Sommertemperatur
    designtemp: Optional[float] = None  # Auslegungstemperatur
    targetflowtemp: Optional[float] = None  # Berechnete Vorlauftemperatur
    minflowtemp: Optional[float] = None  # Min Vorlauf
    maxflowtemp: Optional[float] = None  # Max Vorlauf
    heatingtype: Optional[str] = None  # Heizkörper, Fußboden
    summermode: Optional[str] = None  # Winter, Sommer
    controlmode: Optional[str] = None  # Wetter kompensiert
    nofrostmode: Optional[str] = None  # Frostschutzmodus
    nofrosttemp: Optional[float] = None  # Frostschutztemperatur
    program: Optional[str] = None  # Programm
    control: Optional[str] = None  # RC310

    @classmethod
    def from_api(cls, data: dict) -> "ThermostatHC1":
        d = data or {}
        g = lambda name, default=None: mapped_get(d, name, _HC, default)
        return cls(
            mode=g("mode"),
            modetype=g("modetype"),
            seltemp=to_float(g("seltemp")),
            comforttemp=to_float(g("comforttemp")),
            ecotemp=to_float(g("ecotemp")),
            manualtemp=to_float(g("manualtemp")),
            summertemp=to_float(g("summertemp")),
            designtemp=to_float(g("designtemp")),
            targetflowtemp=to_float(g("targetflowtemp")),
            minflowtemp=to_float(g("minflowtemp")),
            maxflowtemp=to_float(g("maxflowtemp")),
            heatingtype=g("heatingtype"),
            summermode=g("summermode"),
            controlmode=g("controlmode"),
            nofrostmode=g("nofrostmode"),
            nofrosttemp=to_float(g("nofrosttemp")),
            program=g("program"),
            control=g("control"),
        )


@dataclass
class ThermostatWWK:
    """Warmwasserkreis Daten vom Thermostat."""

    mode: Optional[str] = None  # Eigenprog., An, Aus
    settemp: Optional[float] = None  # Solltemperatur
    settemplow: Optional[float] = None  # Untere Solltemperatur
    circmode: Optional[str] = None  # Zirkulationspumpenmodus
    chargeduration: Optional[int] = None  # Ladedauer (min)
    charge: Optional[bool] = None  # Laden aktiv
    disinfecting: Optional[bool] = None  # Desinfektion aktiv
    disinfectday: Optional[str] = None  # Desinfektionstag
    disinfecttime: Optional[int] = None  # Desinfektionszeit (min)
    dailyheating: Optional[bool] = None  # Tägliches Heizen
    dailyheattime: Optional[int] = None  # Tägliche Heizzeit (min)
    extra: Optional[bool] = None  # Extra-Warmwasser (an/aus)

    @classmethod
    def from_api(cls, data: dict) -> "ThermostatWWK":
        d = data or {}
        g = lambda name, default=None: mapped_get(d, name, _WW, default)
        return cls(
            mode=g("mode"),
            settemp=to_float(g("settemp")),
            settemplow=to_float(g("settemplow")),
            circmode=g("circmode"),
            chargeduration=to_int(g("chargeduration")),
            charge=to_bool(g("charge")),
            disinfecting=to_bool(g("disinfecting")),
            disinfectday=g("disinfectday"),
            disinfecttime=to_int(g("disinfecttime")),
            dailyheating=to_bool(g("dailyheating")),
            dailyheattime=to_int(g("dailyheattime")),
            extra=to_bool(g("extra")),
        )


@dataclass
class Thermostat:
    """Thermostat-Daten (RC310) aus /api/thermostat."""

    lastcode: Optional[str] = None  # Letzter Fehlercode
    datetime: Optional[str] = None  # Datum/Zeit
    damped_outdoor_temp: Optional[float] = None  # Gedämpfte Außentemp
    building: Optional[str] = None  # Gebäudetyp
    minexttemp: Optional[float] = None  # Min Außentemperatur

    hc1: Optional[ThermostatHC1] = None
    wwk: Optional[ThermostatWWK] = None

    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> "Thermostat":
        """Erstellt Thermostat aus der /api/thermostat Antwort.

        Normalisiert die Langname-Keys automatisch.
        """
        raw = data or {}
        d = normalize_keys(raw)
        g = lambda name, default=None: mapped_get(d, name, _S, default)

        return cls(
            lastcode=g("lastcode"),
            datetime=g("datetime"),
            damped_outdoor_temp=to_float(g("dampedoutdoortemp")),
            building=g("building"),
            minexttemp=to_float(g("minexttemp")),
            hc1=ThermostatHC1.from_api(d.get("hc1") or {}),
            wwk=ThermostatWWK.from_api(d.get("dhw") or {}),
            raw=raw,
        )
