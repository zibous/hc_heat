CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    mode TEXT,
    outdoor_temp REAL,
    flow_temp REAL,
    flow_set_temp REAL,
    target_flow_temp REAL,
    dhw_temp REAL,
    dhw_set_temp REAL,
    burner_active INTEGER,
    burner_power INTEGER,
    pump_active INTEGER,
    pump_modulation INTEGER,
    energy_total_kwh REAL,
    energy_heat_kwh REAL,
    energy_dhw_kwh REAL,
    gas_display_m3 REAL,
    gas_total_m3 REAL,
    burner_starts INTEGER,
    burner_runtime_min INTEGER,
    heating_starts INTEGER,
    heating_runtime_min INTEGER,
    lastcode_boiler TEXT,
    lastcode_thermostat TEXT
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_ts ON measurements(ts);
