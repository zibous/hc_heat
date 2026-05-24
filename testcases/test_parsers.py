# test_boiler_to_system.py
import json
from lib.models.system_data import SystemData
from lib.models.boiler import Boiler

with open("sample.json", "r", encoding="utf-8") as f:
    full = json.load(f)

# falls snapshot die Boiler-Antwort als Root enthält:
boiler_payload = full.get("boiler") or full
print(
    "BOILER KEYS:",
    (
        list(boiler_payload.keys())
        if isinstance(boiler_payload, dict)
        else type(boiler_payload)
    ),
)
s = SystemData.from_api(boiler_payload)
b = Boiler.from_api(boiler_payload)
print(
    "SystemData parsed:",
    {
        "outdoor": s.outdoor_temp,
        "heating_active": s.heating_active,
        "tapwater": s.tapwater_active,
    },
)
print("Boiler parsed dhw.curtemp:", getattr(b.dhw, "curtemp", None))
