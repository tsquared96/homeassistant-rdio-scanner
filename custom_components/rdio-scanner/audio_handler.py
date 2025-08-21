"""Audio handler for serving database BLOBs."""
import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RdioScannerAudioView(HomeAssistantView):
    """Serve audio files from database BLOBs."""
    
    url = "/api/rdio_scanner/audio/{call_id}"
    name = "api:rdio_scanner:audio"
    requires_auth = True
    
    async def get(self, request: web.Request, call_id: str) -> web.Response:
        """Serve audio file."""
        hass = request.app["hass"]
        
        # Find the coordinator
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                call_id_int = int(call_id)
                audio_data = await coordinator.db.get_call_audio(call_id_int)
                
                if audio_data:
                    return web.Response(
                        body=audio_data['data'],
                        content_type=audio_data['type'],
                        headers={
                            'Content-Disposition': f'inline; filename="{audio_data["name"]}"',
                            'Cache-Control': 'public, max-age=3600',
                        }
                    )
            except Exception as err:
                _LOGGER.error("Error getting audio: %s", err)
        
        return web.Response(status=404, text="Audio not found")


def setup_audio_endpoint(hass: HomeAssistant):
    """Set up audio endpoint."""
    hass.http.register_view(RdioScannerAudioView())
