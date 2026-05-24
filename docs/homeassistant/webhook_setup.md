# Home Assistant Webhook Integration

## Übersicht

Der Heizungscontroller sendet Events per Webhook an Home Assistant bei:

| Event | Auslöser | Payload |
|-------|----------|---------|
| `mode_changed` | Betriebsmodus wechselt | `old_mode`, `new_mode` |
| `error_boiler` | Neuer Kessel-Fehlercode | `code` |
| `error_thermostat` | Neuer Thermostat-Fehlercode | `code` |
| `temp_warning` | WW-Temperatur zu niedrig | `dhw_curtemp`, `threshold` |
| `system_ok` | Temperatur wieder normal | `message` |
| `mqtt_unavailable` | MQTT Broker nicht erreichbar | `message`, `host` |

## 1. Webhook in Home Assistant einrichten

### .env Konfiguration

```env
HA_WEBHOOK_URL=http://10.1.1.217:8123
HA_WEBHOOK_ID=heatcontrol
```

### automation.yaml – Webhook-Trigger

```yaml
automation:
  - alias: "Heizung Webhook Empfänger"
    id: heizung_webhook
    trigger:
      - platform: webhook
        webhook_id: heatcontrol
        allowed_methods:
          - POST
        local_only: true
    action:
      - choose:
          # ── Betriebsmodus geändert ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'mode_changed' }}"
            sequence:
              - service: input_text.set_value
                target:
                  entity_id: input_text.heizung_modus
                data:
                  value: "{{ trigger.json.new_mode }}"
              - service: logbook.log
                data:
                  name: Heizung
                  message: >
                    Modus: {{ trigger.json.old_mode }} → {{ trigger.json.new_mode }}

          # ── Kessel-Fehler ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'error_boiler' }}"
            sequence:
              - service: persistent_notification.create
                data:
                  title: "🔥 Kessel-Fehler"
                  message: "{{ trigger.json.code }}"
                  notification_id: heizung_error_boiler
              - service: notify.notify
                data:
                  title: "🔥 Kessel-Fehler"
                  message: "{{ trigger.json.code }}"

          # ── Thermostat-Fehler ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'error_thermostat' }}"
            sequence:
              - service: persistent_notification.create
                data:
                  title: "🌡️ Thermostat-Fehler"
                  message: "{{ trigger.json.code }}"
                  notification_id: heizung_error_thermostat
              - service: notify.notify
                data:
                  title: "🌡️ Thermostat-Fehler"
                  message: "{{ trigger.json.code }}"

          # ── Temperaturwarnung ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'temp_warning' }}"
            sequence:
              - service: persistent_notification.create
                data:
                  title: "⚠️ WW-Temperatur niedrig"
                  message: >
                    Aktuelle Temperatur: {{ trigger.json.dhw_curtemp }}°C
                    (Schwelle: {{ trigger.json.threshold }}°C)
                  notification_id: heizung_temp_warning
              - service: notify.notify
                data:
                  title: "⚠️ WW-Temperatur niedrig"
                  message: "{{ trigger.json.dhw_curtemp }}°C (< {{ trigger.json.threshold }}°C)"

          # ── System OK ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'system_ok' }}"
            sequence:
              - service: persistent_notification.dismiss
                data:
                  notification_id: heizung_temp_warning
              - service: logbook.log
                data:
                  name: Heizung
                  message: "{{ trigger.json.message }}"

          # ── MQTT nicht erreichbar ──
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'mqtt_unavailable' }}"
            sequence:
              - service: persistent_notification.create
                data:
                  title: "📡 MQTT Broker offline"
                  message: "{{ trigger.json.message }} ({{ trigger.json.host }})"
                  notification_id: heizung_mqtt_error
              - service: notify.notify
                data:
                  title: "📡 MQTT offline"
                  message: "{{ trigger.json.message }}"
```

## 2. Helfer anlegen (optional)

Unter Einstellungen → Geräte & Dienste → Helfer:

| Helfer | Typ | Zweck |
|--------|-----|-------|
| `input_text.heizung_modus` | Text | Aktueller Betriebsmodus |

## 3. Dashboard-Karte (optional)

```yaml
type: entities
title: Heizungscontroller
entities:
  - entity: input_text.heizung_modus
    name: Betriebsmodus
    icon: mdi:fire
```

## 4. Benachrichtigungen anpassen

Die `notify.notify` Aufrufe verwenden den Standard-Notify-Dienst.
Für spezifische Geräte anpassen:

```yaml
# Beispiel: Mobile App
- service: notify.mobile_app_peter
  data:
    title: "🔥 Kessel-Fehler"
    message: "{{ trigger.json.code }}"
    data:
      priority: high
      channel: heizung
```

## 5. Webhook testen

```bash
curl -X POST http://10.1.1.217:8123/api/webhook/heatcontrol \
  -H "Content-Type: application/json" \
  -d '{"event": "mode_changed", "old_mode": "standby", "new_mode": "heating"}'
```

## Payload-Beispiele

### mode_changed
```json
{
  "event": "mode_changed",
  "old_mode": "standby",
  "new_mode": "heating"
}
```

Mögliche Modi: `standby`, `heating`, `dhw`, `disinfection`

### error_boiler
```json
{
  "event": "error_boiler",
  "code": "6L(229) 24.01.2026 17:42 (0 min)"
}
```

### temp_warning
```json
{
  "event": "temp_warning",
  "dhw_curtemp": 32.5,
  "threshold": 35.0
}
```
