"""The Rdio-Scanner integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .rdio_db import RdioScannerDB

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rdio-Scanner from a config entry."""
    coordinator = RdioScannerDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup audio endpoint
    from .audio_handler import setup_audio_endpoint
    setup_audio_endpoint(hass)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.db.close()
    
    return unload_ok


class RdioScannerDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Rdio-Scanner data."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.db = RdioScannerDB(entry.data)
        self.calls = []
        self.systems = []
        self.talkgroups = []
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
    
    async def _async_update_data(self):
        """Fetch data from Rdio-Scanner database."""
        try:
            await self.db.connect()
            
            # Get recent calls
            self.calls = await self.db.get_recent_calls(limit=100)
            
            # Get systems and talkgroups
            self.systems = await self.db.get_systems()
            self.talkgroups = await self.db.get_talkgroups()
            
            # Get active/live calls (calls from last 30 seconds)
            active_calls = [
                call for call in self.calls
                if call.get('dateTime') and self._is_recent(call['dateTime'])
            ]
            
            return {
                "active_calls": len(active_calls),
                "total_calls": len(self.calls),
                "calls": self.calls,
                "systems": self.systems,
                "talkgroups": self.talkgroups,
                "connected": True,
            }
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error communicating with database: {err}")
    
    def _is_recent(self, timestamp, seconds=30):
        """Check if timestamp is within last N seconds."""
        from datetime import datetime, timezone
        try:
            call_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - call_time).total_seconds() < seconds
        except:
            return False
