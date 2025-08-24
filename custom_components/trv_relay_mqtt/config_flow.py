from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, CONF_QOS
from .const import DOMAIN, CONF_DEVICE_TYPE, CONF_COMMAND_TOPIC, CONF_STATE_TOPIC, CONF_CURRENT_TEMP_TOPIC, CONF_TARGET_TEMP_STATE_TOPIC, CONF_RETAIN, CONF_MIN_TEMP, CONF_MAX_TEMP, CONF_WINDOW_SENSORS, CONF_OFF_PAYLOAD, CONF_RESUME_ON_CLOSE, CONF_SIMPLE_GUI, CONF_RELAY_COMMAND_TOPICS, CONF_RELAY_OFF_DELAYS, CONF_RELAY_ON_PAYLOAD, CONF_RELAY_OFF_PAYLOAD

DEVICE_TYPE_TRV = "trv"
DEVICE_TYPE_RELAY = "relay"
DEVICE_TYPE_SELECTOR = vol.In([DEVICE_TYPE_TRV, DEVICE_TYPE_RELAY])

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 4

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_DEVICE_TYPE): DEVICE_TYPE_SELECTOR,
            vol.Required(CONF_COMMAND_TOPIC): str,
            vol.Optional(CONF_STATE_TOPIC): str,
            vol.Optional(CONF_CURRENT_TEMP_TOPIC): str,
            vol.Optional(CONF_TARGET_TEMP_STATE_TOPIC): str,
            vol.Optional(CONF_WINDOW_SENSORS): str,
            vol.Optional(CONF_OFF_PAYLOAD, default="OFF"): str,
            vol.Optional(CONF_RESUME_ON_CLOSE, default=True): bool,
            vol.Optional(CONF_SIMPLE_GUI, default=True): bool,
            vol.Optional(CONF_RELAY_COMMAND_TOPICS): str,
            vol.Optional(CONF_RELAY_OFF_DELAYS): str,
            vol.Optional(CONF_RELAY_ON_PAYLOAD, default="ON"): str,
            vol.Optional(CONF_RELAY_OFF_PAYLOAD, default="OFF"): str,
            vol.Optional(CONF_QOS, default=0): int,
            vol.Optional(CONF_RETAIN, default=False): bool,
            vol.Optional(CONF_MIN_TEMP, default=5.0): float,
            vol.Optional(CONF_MAX_TEMP, default=30.0): float,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @callback
    def async_get_options_flow(self, config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.config_entry.data, **(self.config_entry.options or {})}
        schema = vol.Schema({
            vol.Optional(CONF_QOS, default=data.get(CONF_QOS, 0)): int,
            vol.Optional(CONF_RETAIN, default=data.get(CONF_RETAIN, False)): bool,
            vol.Optional(CONF_MIN_TEMP, default=data.get(CONF_MIN_TEMP, 5.0)): float,
            vol.Optional(CONF_MAX_TEMP, default=data.get(CONF_MAX_TEMP, 30.0)): float,
            vol.Optional(CONF_WINDOW_SENSORS, default=data.get(CONF_WINDOW_SENSORS, "")): str,
            vol.Optional(CONF_OFF_PAYLOAD, default=data.get(CONF_OFF_PAYLOAD, "OFF")): str,
            vol.Optional(CONF_RESUME_ON_CLOSE, default=data.get(CONF_RESUME_ON_CLOSE, True)): bool,
            vol.Optional(CONF_SIMPLE_GUI, default=data.get(CONF_SIMPLE_GUI, True)): bool,
            vol.Optional(CONF_RELAY_COMMAND_TOPICS, default=data.get(CONF_RELAY_COMMAND_TOPICS, "")): str,
            vol.Optional(CONF_RELAY_OFF_DELAYS, default=data.get(CONF_RELAY_OFF_DELAYS, "")): str,
            vol.Optional(CONF_RELAY_ON_PAYLOAD, default=data.get(CONF_RELAY_ON_PAYLOAD, "ON")): str,
            vol.Optional(CONF_RELAY_OFF_PAYLOAD, default=data.get(CONF_RELAY_OFF_PAYLOAD, "OFF")): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
