"""Sensor platform for Rdio-Scanner."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rdio-Scanner sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        RdioScannerActiveCalls(coordinator, config_entry),
        RdioScannerTotalCalls(coordinator, config_entry),
        RdioScannerSystems(coordinator, config_entry),
        RdioScannerTalkgroups(coordinator, config_entry),
    ]
    
    async_add_entities(sensors)


class RdioScannerSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Rdio-Scanner sensors."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data.get(CONF_NAME, "Rdio-Scanner"),
            "manufacturer": "Rdio-Scanner",
            "model": "Radio Scanner",
        }


class RdioScannerActiveCalls(RdioScannerSensorBase):
    """Sensor for active calls."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Active Calls"
        self._attr_unique_id = f"{config_entry.entry_id}_active_calls"
        self._attr_icon = "mdi:radio-tower"
    
    @property
    def state(self):
        """Return the state."""
        return self.coordinator.data.get("active_calls", 0)


class RdioScannerTotalCalls(RdioScannerSensorBase):
    """Sensor for total calls."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Total Calls"
        self._attr_unique_id = f"{config_entry.entry_id}_total_calls"
        self._attr_icon = "mdi:counter"
    
    @property
    def state(self):
        """Return the state."""
        return self.coordinator.data.get("total_calls", 0)
    
    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        calls = self.coordinator.data.get("calls", [])
        if calls and len(calls) > 0:
            latest = calls[0]
            return {
                "latest_talkgroup": latest.get("talkgroup_name", ""),
                "latest_time": latest.get("timestamp", ""),
                "latest_length": latest.get("call_length", 0),
            }
        return {}


class RdioScannerSystems(RdioScannerSensorBase):
    """Sensor for systems count."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Systems"
        self._attr_unique_id = f"{config_entry.entry_id}_systems"
        self._attr_icon = "mdi:radio"
    
    @property
    def state(self):
        """Return the state."""
        return len(self.coordinator.data.get("systems", []))


class RdioScannerTalkgroups(RdioScannerSensorBase):
    """Sensor for talkgroups count."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Talkgroups"
        self._attr_unique_id = f"{config_entry.entry_id}_talkgroups"
        self._attr_icon = "mdi:account-group"
    
    @property
    def state(self):
        """Return the state."""
        return len(self.coordinator.data.get("talkgroups", []))
