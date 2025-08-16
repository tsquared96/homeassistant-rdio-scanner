"""Sensor platform for TrunkRecorder."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrunkRecorderCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrunkRecorder sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    sensors = [
        TrunkRecorderActiveCalls(coordinator),
        TrunkRecorderTotalCalls(coordinator),
    ]
    
    # Add system-specific sensors
    for system in coordinator.systems:
        sensors.append(TrunkRecorderSystemSensor(coordinator, system))
    
    async_add_entities(sensors)


class TrunkRecorderSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for TrunkRecorder sensors."""
    
    def __init__(self, coordinator: TrunkRecorderCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True


class TrunkRecorderActiveCalls(TrunkRecorderSensorBase):
    """Sensor for active calls."""
    
    def __init__(self, coordinator: TrunkRecorderCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_active_calls"
        self._attr_name = "Active Calls"
        self._attr_icon = "mdi:radio-tower"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def state(self):
        """Return the state of the sensor."""
        return len(self.coordinator.active_calls)
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "calls": list(self.coordinator.active_calls.values()),
        }


class TrunkRecorderTotalCalls(TrunkRecorderSensorBase):
    """Sensor for total calls today."""
    
    def __init__(self, coordinator: TrunkRecorderCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_total_calls"
        self._attr_name = "Total Calls Today"
        self._attr_icon = "mdi:counter"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
    
    @property
    def state(self):
        """Return the state of the sensor."""
        # Count calls from today
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        today_calls = [
            call for call in self.coordinator.call_history
            if datetime.fromisoformat(call.get("start_time", "")).date() == today
        ]
        return len(today_calls)


class TrunkRecorderSystemSensor(TrunkRecorderSensorBase):
    """Sensor for a specific system."""
    
    def __init__(
        self, coordinator: TrunkRecorderCoordinator, system: dict
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.system = system
        self._attr_unique_id = f"{DOMAIN}_system_{system['id']}"
        self._attr_name = f"System {system['name']}"
        self._attr_icon = "mdi:radio"
    
    @property
    def state(self):
        """Return the state of the sensor."""
        # Count active calls for this system
        active = sum(
            1 for call in self.coordinator.active_calls.values()
            if call.get("system") == self.system["id"]
        )
        return active
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "system_id": self.system["id"],
            "system_name": self.system["name"],
            "talkgroups": self.coordinator.talkgroups.get(self.system["id"], []),
        }
