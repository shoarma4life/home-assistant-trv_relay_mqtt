from __future__ import annotations
import logging
from typing import Optional, List
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVAC_MODE_HEAT, HVAC_MODE_OFF, SUPPORT_TARGET_TEMPERATURE
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.components import mqtt
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, CONF_QOS
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_COMMAND_TOPIC, CONF_CURRENT_TEMP_TOPIC, CONF_TARGET_TEMP_STATE_TOPIC, CONF_RETAIN, CONF_MIN_TEMP, CONF_MAX_TEMP, CONF_WINDOW_SENSORS, CONF_OFF_PAYLOAD, CONF_RESUME_ON_CLOSE, CONF_SIMPLE_GUI, DATA_COORDINATOR, HEAT_HYSTERESIS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data = {**entry.data, **entry.options}
    if data.get("device_type") != "trv":
        return
    async_add_entities([MqttTRV(hass, entry)], True)

class MqttTRV(ClimateEntity):
    _attr_supported_features = SUPPORT_TARGET_TEMPERATURE
    _attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        d = {**entry.data, **entry.options}
        self._name = d.get(CONF_NAME)
        self._command_topic = d.get(CONF_COMMAND_TOPIC)
        self._current_temp_topic = d.get(CONF_CURRENT_TEMP_TOPIC)
        self._target_temp_state_topic = d.get(CONF_TARGET_TEMP_STATE_TOPIC)
        self._retain = d.get(CONF_RETAIN, False)
        self._qos = d.get(CONF_QOS, 0)
        self._min_temp = d.get(CONF_MIN_TEMP, 5.0)
        self._max_temp = d.get(CONF_MAX_TEMP, 30.0)

        self._window_sensors: List[str] = self._parse_list(d.get(CONF_WINDOW_SENSORS, ""))
        self._off_payload: str = d.get(CONF_OFF_PAYLOAD, "OFF")
        self._resume_on_close: bool = d.get(CONF_RESUME_ON_CLOSE, True)
        self._simple_gui: bool = d.get(CONF_SIMPLE_GUI, True)

        self._current_temperature: Optional[float] = None
        self._target_temperature: Optional[float] = None
        self._last_set_target_temperature: Optional[float] = None
        self._hvac_mode = HVAC_MODE_HEAT
        self._window_open = False

        self._unsubs: list[callable] = []

    def _parse_list(self, s: str) -> List[str]:
        return [x.strip() for x in s.split(",") if x.strip()] if s else []

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"{self._entry.entry_id}_trv"
    @property
    def should_poll(self): return False
    @property
    def current_temperature(self): return self._current_temperature
    @property
    def target_temperature(self): return self._target_temperature
    @property
    def min_temp(self): return self._min_temp
    @property
    def max_temp(self): return self._max_temp
    @property
    def hvac_mode(self): return HVAC_MODE_OFF if self._window_open else self._hvac_mode

    def _heating(self) -> bool:
        if self._window_open: return False
        if self._target_temperature is None or self._current_temperature is None: return False
        return (self._target_temperature - self._current_temperature) > HEAT_HYSTERESIS

    def _notify(self):
        coord = self.hass.data.get(DOMAIN, {}).get(DATA_COORDINATOR)
        if coord:
            coord.set_trv(self.unique_id, self._heating())

    async def async_added_to_hass(self):
        if self._current_temp_topic:
            self._unsubs.append(await mqtt.async_subscribe(self.hass, self._current_temp_topic, self._on_curr, qos=self._qos))
        if self._target_temp_state_topic:
            self._unsubs.append(await mqtt.async_subscribe(self.hass, self._target_temp_state_topic, self._on_targ, qos=self._qos))
        if self._window_sensors:
            self._unsubs.append(async_track_state_change_event(self.hass, self._window_sensors, self._on_window))
        self._notify()

    async def async_will_remove_from_hass(self):
        for u in self._unsubs:
            try: u()
            except: pass
        self._unsubs.clear()
        self._notify()

    @callback
    def _on_curr(self, msg):
        try:
            self._current_temperature = float(msg.payload)
            self._notify()
            self.async_write_ha_state()
        except ValueError:
            _LOGGER.warning("Invalid current temperature payload: %s", msg.payload)

    @callback
    def _on_targ(self, msg):
        try:
            self._target_temperature = float(msg.payload)
            self._notify()
            self.async_write_ha_state()
        except ValueError:
            _LOGGER.warning("Invalid target temperature payload: %s", msg.payload)

    @callback
    def _on_window(self, event):
        was = self._window_open
        any_open = False
        for eid in self._window_sensors:
            st = self.hass.states.get(eid)
            if st and (st.state or "").lower() in ("on","open","true"):
                any_open = True; break
        self._window_open = any_open
        if was!=any_open:
            if any_open:
                self.hass.async_create_task(mqtt.async_publish(self.hass, self._command_topic, self._off_payload, qos=self._qos, retain=self._retain))
            else:
                if self._resume_on_close and self._last_set_target_temperature is not None:
                    self.hass.async_create_task(mqtt.async_publish(self.hass, self._command_topic, str(self._last_set_target_temperature), qos=self._qos, retain=self._retain))
            self._notify()
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        t = kwargs.get(ATTR_TEMPERATURE)
        if t is None: return
        self._target_temperature = float(t)
        self._last_set_target_temperature = self._target_temperature
        if not self._window_open:
            await mqtt.async_publish(self.hass, self._command_topic, str(self._target_temperature), qos=self._qos, retain=self._retain)
        self._notify()
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        if hvac_mode == HVAC_MODE_OFF:
            await mqtt.async_publish(self.hass, self._command_topic, self._off_payload, qos=self._qos, retain=self._retain)
        elif hvac_mode == HVAC_MODE_HEAT and not self._window_open:
            if self._last_set_target_temperature is not None:
                await mqtt.async_publish(self.hass, self._command_topic, str(self._last_set_target_temperature), qos=self._qos, retain=self._retain)
        self._notify()
        self.async_write_ha_state()
