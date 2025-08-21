"""Media player for Rdio-Scanner."""
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
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
    """Set up Rdio-Scanner media player."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([RdioScannerMediaPlayer(coordinator, config_entry)])


class RdioScannerMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media player for Rdio-Scanner calls."""
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize media player."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_player"
        self._attr_name = f"{config_entry.data.get(CONF_NAME)} Player"
        self._attr_icon = "mdi:radio"
        self._attr_media_content_type = MediaType.MUSIC
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data.get(CONF_NAME, "Rdio-Scanner"),
            "manufacturer": "Rdio-Scanner",
        }
        self._current_call = None
        self._state = MediaPlayerState.IDLE
    
    @property
    def state(self):
        """Return the state of the player."""
        return self._state
    
    @property
    def media_title(self):
        """Return the title of current media."""
        if self._current_call:
            return self._current_call.get("talkgroup_name", "Unknown")
        return None
    
    @property
    def media_artist(self):
        """Return the artist of current media."""
        if self._current_call:
            return f"System {self._current_call.get('system', 'Unknown')}"
        return None
    
    async def async_play_media(self, media_type: str, media_id: str, **kwargs):
        """Play a specific call."""
        # Find the call in the coordinator data
        calls = self.coordinator.data.get("calls", [])
        for call in calls:
            if str(call.get("id")) == media_id:
                self._current_call = call
                self._state = MediaPlayerState.PLAYING
                self.async_write_ha_state()
                break
