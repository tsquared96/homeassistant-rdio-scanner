"""Constants for TrunkRecorder integration."""
from datetime import timedelta

DOMAIN = "trunk_recorder"
DEFAULT_NAME = "Trunk Recorder"
DEFAULT_PORT = 3000
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

CONF_API_KEY = "api_key"
CONF_SYSTEMS = "systems"
CONF_TALKGROUPS = "talkgroups"

# WebSocket events
WS_TYPE_CALL_START = "call_start"
WS_TYPE_CALL_END = "call_end"
WS_TYPE_CALL_UPDATE = "call_update"

# Attributes
ATTR_TALKGROUP = "talkgroup"
ATTR_TALKGROUP_NAME = "talkgroup_name"
ATTR_SYSTEM = "system"
ATTR_FREQUENCY = "frequency"
ATTR_EMERGENCY = "emergency"
ATTR_ENCRYPTED = "encrypted"
ATTR_UNITS = "units"
ATTR_TRANSCRIPT = "transcript"
ATTR_AUDIO_URL = "audio_url"
ATTR_START_TIME = "start_time"
ATTR_STOP_TIME = "stop_time"
ATTR_CALL_LENGTH = "call_length"
