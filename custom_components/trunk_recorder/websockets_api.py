"""WebSocket API for TrunkRecorder."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_websocket_api(hass: HomeAssistant, entry_id: str) -> None:
    """Set up the WebSocket API."""
    websocket_api.async_register_command(hass, ws_get_calls)
    websocket_api.async_register_command(hass, ws_get_systems)
    websocket_api.async_register_command(hass, ws_get_history)
    websocket_api.async_register_command(hass, ws_get_statistics)
    websocket_api.async_register_command(hass, ws_play_call)
    websocket_api.async_register_command(hass, ws_get_talkgroups)
    websocket_api.async_register_command(hass, ws_set_filter)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/get_calls",
        vol.Optional("system_id"): str,
        vol.Optional("talkgroup_id"): str,
        vol.Optional("limit", default=50): int,
        vol.Optional("active_only", default=False): bool,
    }
)
@callback
def ws_get_calls(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Get call history or active calls."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    if msg.get("active_only"):
        calls = list(coordinator.active_calls.values())
    else:
        calls = coordinator.call_history
    
    # Filter by system if requested
    if system_id := msg.get("system_id"):
        calls = [c for c in calls if c.get("system") == system_id]
    
    # Filter by talkgroup if requested
    if talkgroup_id := msg.get("talkgroup_id"):
        calls = [c for c in calls if c.get("talkgroup") == talkgroup_id]
    
    # Limit results
    calls = calls[:msg["limit"]]
    
    connection.send_result(msg["id"], calls)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/get_systems",
    }
)
@callback
def ws_get_systems(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Get systems list."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    systems_data = []
    for system in coordinator.systems:
        system_info = {
            "id": system["id"],
            "name": system["name"],
            "type": system.get("type", "unknown"),
            "talkgroups": coordinator.talkgroups.get(system["id"], []),
            "active_calls": sum(
                1 for call in coordinator.active_calls.values()
                if call.get("system") == system["id"]
            ),
        }
        systems_data.append(system_info)
    
    connection.send_result(msg["id"], systems_data)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/get_history",
        vol.Optional("limit", default=100): int,
        vol.Optional("offset", default=0): int,
        vol.Optional("start_time"): str,
        vol.Optional("end_time"): str,
        vol.Optional("system_id"): str,
        vol.Optional("talkgroup_id"): str,
        vol.Optional("search"): str,
    }
)
@callback
def ws_get_history(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Get filtered call history."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    calls = coordinator.call_history.copy()
    
    # Filter by time range if specified
    if start_time := msg.get("start_time"):
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time)
        calls = [
            c for c in calls
            if datetime.fromisoformat(c.get("start_time", "")) >= start_dt
        ]
    
    if end_time := msg.get("end_time"):
        from datetime import datetime
        end_dt = datetime.fromisoformat(end_time)
        calls = [
            c for c in calls
            if datetime.fromisoformat(c.get("start_time", "")) <= end_dt
        ]
    
    # Filter by system
    if system_id := msg.get("system_id"):
        calls = [c for c in calls if c.get("system") == system_id]
    
    # Filter by talkgroup
    if talkgroup_id := msg.get("talkgroup_id"):
        calls = [c for c in calls if c.get("talkgroup") == talkgroup_id]
    
    # Search in talkgroup names and transcripts
    if search := msg.get("search"):
        search_lower = search.lower()
        calls = [
            c for c in calls
            if search_lower in c.get("talkgroup_name", "").lower()
            or search_lower in c.get("transcript", "").lower()
            or search_lower in str(c.get("units", [])).lower()
        ]
    
    # Apply pagination
    offset = msg.get("offset", 0)
    limit = msg.get("limit", 100)
    total = len(calls)
    calls = calls[offset:offset + limit]
    
    connection.send_result(
        msg["id"],
        {
            "calls": calls,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/get_statistics",
        vol.Optional("system_id"): str,
        vol.Optional("period", default="today"): str,  # today, week, month, all
    }
)
@callback
def ws_get_statistics(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Get call statistics."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    from datetime import datetime, timedelta, timezone
    
    # Determine time range
    now = datetime.now(timezone.utc)
    period = msg.get("period", "today")
    
    if period == "today":
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_time = now - timedelta(days=7)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:  # all
        start_time = datetime.min.replace(tzinfo=timezone.utc)
    
    # Filter calls by time and system
    filtered_calls = []
    for call in coordinator.call_history:
        try:
            call_time = datetime.fromisoformat(call.get("start_time", ""))
            if call_time >= start_time:
                if system_id := msg.get("system_id"):
                    if call.get("system") == system_id:
                        filtered_calls.append(call)
                else:
                    filtered_calls.append(call)
        except:
            continue
    
    # Calculate statistics
    total_calls = len(filtered_calls)
    total_airtime = sum(
        call.get("call_length", 0) for call in filtered_calls
    )
    
    # Get unique talkgroups
    unique_talkgroups = set(
        call.get("talkgroup") for call in filtered_calls
        if call.get("talkgroup")
    )
    
    # Get top talkgroups
    talkgroup_counts = {}
    for call in filtered_calls:
        tg = call.get("talkgroup")
        if tg:
            talkgroup_counts[tg] = talkgroup_counts.get(tg, 0) + 1
    
    top_talkgroups = sorted(
        talkgroup_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]
    
    # Emergency calls
    emergency_calls = sum(
        1 for call in filtered_calls if call.get("emergency")
    )
    
    # Encrypted calls
    encrypted_calls = sum(
        1 for call in filtered_calls if call.get("encrypted")
    )
    
    stats = {
        "total_calls": total_calls,
        "total_airtime": total_airtime,
        "unique_talkgroups": len(unique_talkgroups),
        "active_calls": len(coordinator.active_calls),
        "active_systems": len(coordinator.systems),
        "emergency_calls": emergency_calls,
        "encrypted_calls": encrypted_calls,
        "top_talkgroups": [
            {
                "id": tg_id,
                "count": count,
                "name": next(
                    (
                        tg.get("name", tg_id)
                        for system_tgs in coordinator.talkgroups.values()
                        for tg in system_tgs
                        if tg.get("id") == tg_id
                    ),
                    tg_id,
                ),
            }
            for tg_id, count in top_talkgroups
        ],
        "period": period,
    }
    
    connection.send_result(msg["id"], stats)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/play_call",
        vol.Required("call_id"): str,
    }
)
@callback
def ws_play_call(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Play a specific call."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    # Find the call in active or history
    call = coordinator.active_calls.get(msg["call_id"])
    if not call:
        for historical_call in coordinator.call_history:
            if historical_call.get("id") == msg["call_id"]:
                call = historical_call
                break
    
    if call:
        audio_url = f"http://{coordinator.host}:{coordinator.port}/api/calls/{msg['call_id']}/audio"
        
        # Update media player if it exists
        media_player = hass.states.get("media_player.trunk_recorder_player")
        if media_player:
            hass.async_create_task(
                hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": "media_player.trunk_recorder_player",
                        "media_content_type": "audio/mp3",
                        "media_content_id": audio_url,
                    },
                )
            )
        
        connection.send_result(
            msg["id"],
            {
                "audio_url": audio_url,
                "call": call,
            }
        )
    else:
        connection.send_error(
            msg["id"],
            "call_not_found",
            f"Call with ID {msg['call_id']} not found",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/get_talkgroups",
        vol.Required("system_id"): str,
    }
)
@callback
def ws_get_talkgroups(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Get talkgroups for a specific system."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    
    talkgroups = coordinator.talkgroups.get(msg["system_id"], [])
    
    # Add call counts for each talkgroup
    for tg in talkgroups:
        tg["active_calls"] = sum(
            1 for call in coordinator.active_calls.values()
            if call.get("talkgroup") == tg.get("id")
        )
        tg["recent_calls"] = sum(
            1 for call in coordinator.call_history[:100]
            if call.get("talkgroup") == tg.get("id")
        )
    
    connection.send_result(msg["id"], talkgroups)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "trunk_recorder/set_filter",
        vol.Optional("system_id"): str,
        vol.Optional("talkgroup_ids"): [str],
        vol.Optional("enable_notifications", default=True): bool,
    }
)
@callback
def ws_set_filter(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    """Set filtering preferences for the current session."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    
    # Store filter preferences in hass.data for this connection
    if "filters" not in hass.data[DOMAIN][entry_id]:
        hass.data[DOMAIN][entry_id]["filters"] = {}
    
    connection_id = id(connection)
    hass.data[DOMAIN][entry_id]["filters"][connection_id] = {
        "system_id": msg.get("system_id"),
        "talkgroup_ids": msg.get("talkgroup_ids", []),
        "enable_notifications": msg.get("enable_notifications", True),
    }
    
    connection.send_result(msg["id"], {"status": "ok"})
