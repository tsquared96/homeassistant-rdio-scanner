"""DataUpdateCoordinator for TrunkRecorder."""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import websockets

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, WS_TYPE_CALL_START, WS_TYPE_CALL_END, WS_TYPE_CALL_UPDATE

_LOGGER = logging.getLogger(__name__)


class TrunkRecorderCoordinator(DataUpdateCoordinator):
    """Coordinator for TrunkRecorder data."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.session = session
        self.host = host
        self.port = port
        self.websocket = None
        self.websocket_task = None
        self.active_calls = {}
        self.call_history = []
        self.systems = []
        self.talkgroups = {}
    
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Fetch systems
            async with self.session.get(
                f"http://{self.host}:{self.port}/api/systems"
            ) as response:
                response.raise_for_status()
                self.systems = await response.json()
            
            # Fetch active calls
            async with self.session.get(
                f"http://{self.host}:{self.port}/api/calls/active"
            ) as response:
                response.raise_for_status()
                active_calls_list = await response.json()
                self.active_calls = {call["id"]: call for call in active_calls_list}
            
            # Fetch recent calls
            async with self.session.get(
                f"http://{self.host}:{self.port}/api/calls?limit=100"
            ) as response:
                response.raise_for_status()
                self.call_history = await response.json()
            
            # Fetch talkgroups for each system
            for system in self.systems:
                async with self.session.get(
                    f"http://{self.host}:{self.port}/api/systems/{system['id']}/talkgroups"
                ) as response:
                    response.raise_for_status()
                    self.talkgroups[system['id']] = await response.json()
            
            return {
                "active_calls": self.active_calls,
                "call_history": self.call_history,
                "systems": self.systems,
                "talkgroups": self.talkgroups,
            }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
    
    async def start_websocket(self):
        """Start WebSocket connection for real-time updates."""
        self.websocket_task = asyncio.create_task(self._websocket_loop())
    
    async def stop_websocket(self):
        """Stop WebSocket connection."""
        if self.websocket_task:
            self.websocket_task.cancel()
            try:
                await self.websocket_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
    
    async def _websocket_loop(self):
        """WebSocket loop for real-time updates."""
        while True:
            try:
                async with websockets.connect(
                    f"ws://{self.host}:{self.port}/ws"
                ) as websocket:
                    self.websocket = websocket
                    _LOGGER.info("Connected to TrunkRecorder WebSocket")
                    
                    async for message in websocket:
                        data = json.loads(message)
                        await self._handle_websocket_message(data)
            except Exception as err:
                _LOGGER.error("WebSocket error: %s", err)
                await asyncio.sleep(10)
    
    async def _handle_websocket_message(self, data: dict):
        """Handle WebSocket message."""
        msg_type = data.get("type")
        
        if msg_type == WS_TYPE_CALL_START:
            call_data = data.get("call")
            self.active_calls[call_data["id"]] = call_data
            self.hass.bus.async_fire(
                f"{DOMAIN}_call_start",
                call_data,
            )
        elif msg_type == WS_TYPE_CALL_END:
            call_id = data.get("call_id")
            if call_id in self.active_calls:
                call_data = self.active_calls.pop(call_id)
                self.call_history.insert(0, call_data)
                if len(self.call_history) > 100:
                    self.call_history = self.call_history[:100]
                self.hass.bus.async_fire(
                    f"{DOMAIN}_call_end",
                    call_data,
                )
        elif msg_type == WS_TYPE_CALL_UPDATE:
            call_data = data.get("call")
            call_id = call_data.get("id")
            if call_id in self.active_calls:
                self.active_calls[call_id].update(call_data)
        
        await self.async_request_refresh()
    
    async def get_audio_url(self, call_id: str) -> str:
        """Get audio URL for a call."""
        return f"http://{self.host}:{self.port}/api/calls/{call_id}/audio"
