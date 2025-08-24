from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import List, Dict
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.components import mqtt
from .const import DOMAIN, DATA_COORDINATOR, CONF_RELAY_COMMAND_TOPICS, CONF_RELAY_OFF_DELAYS, CONF_RELAY_ON_PAYLOAD, CONF_RELAY_OFF_PAYLOAD, CONF_QOS, CONF_RETAIN

PLATFORMS = ["climate","switch"]

@dataclass
class RelayCfg:
    topic: str
    delay: int

class Coordinator:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.relays: List[RelayCfg] = []
        self.on_payload = "ON"; self.off_payload = "OFF"
        self.qos = 0; self.retain = False
        self.trv_demand: Dict[str,bool] = {}
        self._off_tasks: Dict[str,asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def configure(self, topics: List[str], delays: List[int], on_payload: str, off_payload: str, qos: int, retain: bool):
        self.relays = [RelayCfg(t.strip(), delays[i] if i < len(delays) else 0) for i,t in enumerate(topics) if t.strip()]
        self.on_payload = on_payload or "ON"
        self.off_payload = off_payload or "OFF"
        self.qos = qos; self.retain = retain

    @callback
    def set_trv(self, trv_id: str, heating: bool):
        self.trv_demand[trv_id] = bool(heating)
        self.hass.async_create_task(self._recompute())

    async def _pub(self, topic, payload):
        await mqtt.async_publish(self.hass, topic, payload, qos=self.qos, retain=self.retain)

    async def _recompute(self):
        async with self._lock:
            any_on = any(self.trv_demand.values())
            if any_on:
                # cancel scheduled offs and turn on
                for t in list(self._off_tasks.values()):
                    t.cancel()
                self._off_tasks.clear()
                for r in self.relays:
                    await self._pub(r.topic, self.on_payload)
            else:
                # schedule offs
                for r in self.relays:
                    if r.topic in self._off_tasks and not self._off_tasks[r.topic].done():
                        continue
                    self._off_tasks[r.topic] = self.hass.async_create_task(self._delayed_off(r))

    async def _delayed_off(self, r: RelayCfg):
        try:
            if r.delay>0:
                await asyncio.sleep(r.delay)
            await self._pub(r.topic, self.off_payload)
        except asyncio.CancelledError:
            return

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_COORDINATOR] = Coordinator(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = {**entry.data, **entry.options}
    topics = [t.strip() for t in (data.get(CONF_RELAY_COMMAND_TOPICS,"") or "").split(",") if t.strip()]
    delays = []
    raw = (data.get(CONF_RELAY_OFF_DELAYS,"") or "").split(",")
    for d in raw:
        d=d.strip()
        if not d: continue
        try: delays.append(int(d))
        except: delays.append(0)
    onp = data.get(CONF_RELAY_ON_PAYLOAD,"ON")
    offp = data.get(CONF_RELAY_OFF_PAYLOAD,"OFF")
    qos = int(data.get(CONF_QOS,0) or 0)
    retain = bool(data.get(CONF_RETAIN,False))

    coord: Coordinator = hass.data[DOMAIN][DATA_COORDINATOR]
    if topics:
        coord.configure(topics, delays, onp, offp, qos, retain)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
