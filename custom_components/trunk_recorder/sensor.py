"""Sensor platform for Trunk Recorder."""
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
    """Set up Trunk Recorder sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        TrunkRecorderActiveCalls(coordinator, config_entry),
        TrunkRecorderTotalCalls(coordinator, config_entry),
        TrunkRecorderStatus(coordinator, config_entry),
    ]
    
    async_add_entities(sensors)


class TrunkRecorderSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Trunk Recorder sensors."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data.get(CONF_NAME, "Trunk Recorder"),
            "manufacturer": "Trunk Recorder",
            "model": "Database Scanner",
        }


class TrunkRecorderActiveCalls(TrunkRecorderSensorBase):
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


class TrunkRecorderTotalCalls(TrunkRecorderSensorBase):
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


class TrunkRecorderStatus(TrunkRecorderSensorBase):
    """Sensor for connection status."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Status"
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._attr_icon = "mdi:database"
    
    @property
    def state(self):
        """Return the state."""
        return "Connected" if self.coordinator.data.get("connected", False) else "Disconnected"
    
    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "database_type": self.config_entry.data.get("db_type", "unknown"),
            "host": self.config_entry.data.get("host", "unknown"),
            "database": self.config_entry.data.get("db_name", "unknown"),
            "systems": len(self.coordinator.data.get("systems", [])),
        }
