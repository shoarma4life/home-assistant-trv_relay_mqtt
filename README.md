# TRV & Relay over MQTT

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/v/release/shoarma4life/home-assistant-trv_relay_mqtt)](https://github.com/shoarma4life/home-assistant-trv_relay_mqtt/releases)

Een lichte Home Assistant integratie om **thermostatische radiatorkranen (TRV)** en **relais** via **MQTT** te regelen.

## ✨ Functies
- **Optie 1 GUI** → minimalistische weergave, geen boost-knoppen
- **Raamkoppeling** → TRV uit bij open raam, herstel setpoint bij sluiten
- TRV als `climate`-entity, relais als `switch`-entity
- Volledige configuratie via de Home Assistant UI
- Klaar voor **HACS-installatie**

## 🚀 Installatie
### Handmatig
1. Download de laatste [release](https://github.com/shoarma4life/home-assistant-trv_relay_mqtt/releases).
2. Pak de ZIP uit in:
   ```
   config/custom_components/trv_relay_mqtt/
   ```
3. Herstart Home Assistant.
4. Voeg de integratie toe via **Instellingen → Apparaten & Diensten → Integratie toevoegen**.

### Via HACS (nadat je de repo publiceert)
1. Voeg de repo als **custom repository** toe in HACS.
2. Zoek naar **TRV & Relay over MQTT**.
3. Installeer, herstart HA, en voeg de integratie toe.

## ⚙️ Configuratievelden (TRV)
| Veld                     | Beschrijving                                        |
|-------------------------|-----------------------------------------------------|
| `command_topic`         | MQTT-topic voor setpoint / OFF                      |
| `current_temp_topic`    | MQTT-topic voor huidige temperatuur                |
| `target_temp_state_topic` | *(optioneel)*: topic voor feedback setpoint      |
| `window_sensors`        | Komma-gescheiden lijst van sensoren (entity_id's)   |
| `off_payload`           | Payload voor uitzetten bij open raam (default `OFF`)|
| `resume_on_close`       | Herstel setpoint zodra alle ramen dicht zijn        |
| `simple_gui`            | Activeert Optie 1 GUI (geen boost)                  |

## 📦 MQTT Voorbeeld
**TRV**:
```yaml
command_topic: home/trv/keuken/set_temp      # stuur bijv. '21.5' of 'OFF'
current_temp_topic: home/trv/keuken/current_temp
target_temp_state_topic: home/trv/keuken/target_temp
```

**Relay**:
```yaml
command_topic: home/relay/pomp/command      # stuur 'ON'/'OFF'
state_topic:   home/relay/pomp/state        # ontvangt 'ON'/'OFF' of '1'/'0'
```

## 🧾 Licentie
[MIT](LICENSE)
