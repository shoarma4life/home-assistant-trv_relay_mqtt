from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.components import mqtt
from homeassistant.core import callback

async def async_setup_entry(hass, entry, async_add_entities):
    d = {**entry.data, **entry.options}
    if d.get("device_type") != "relay":
        return
    async_add_entities([MqttRelay(hass, entry)], True)

class MqttRelay(SwitchEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        d = {**entry.data, **entry.options}
        self._name = d.get("name")
        self._command_topic = d.get("command_topic")
        self._state_topic = d.get("state_topic")
        self._retain = d.get("retain", False)
        self._qos = d.get("qos", 0)
        self._is_on = False
        self._unsub = None

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"{self._entry.entry_id}_relay"
    @property
    def is_on(self): return self._is_on
    @property
    def should_poll(self): return False

    async def async_added_to_hass(self):
        if self._state_topic:
            self._unsub = await mqtt.async_subscribe(self.hass, self._state_topic, self._on_msg, qos=self._qos)

    async def async_will_remove_from_hass(self):
        if self._unsub: self._unsub(); self._unsub = None

    @callback
    def _on_msg(self, msg):
        p = (msg.payload or "").strip().lower()
        if p in ("1","on","true"): self._is_on = True
        elif p in ("0","off","false"): self._is_on = False
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        await mqtt.async_publish(self.hass, self._command_topic, "ON", qos=self._qos, retain=self._retain)

    async def async_turn_off(self, **kwargs):
        await mqtt.async_publish(self.hass, self._command_topic, "OFF", qos=self._qos, retain=self._retain)
