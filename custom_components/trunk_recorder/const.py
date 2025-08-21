"""Constants for the Trunk Recorder integration."""

DOMAIN = "trunk_recorder"

# Configuration constants
DEFAULT_NAME = "Trunk Recorder"
DEFAULT_DB_NAME = "trunk_recorder"
DEFAULT_PORT_MYSQL = 3306
DEFAULT_PORT_POSTGRES = 5432

# Config keys
CONF_DB_TYPE = "db_type"
CONF_DB_NAME = "db_name"

# Database field mappings
DB_FIELDS = {
    "calls": {
        "id": "id",
        "start_time": "start_time",
        "stop_time": "stop_time", 
        "call_length": "length",
        "talkgroup": "talkgroup",
        "talkgroup_alpha_tag": "talkgroup_alpha_tag",
        "frequency": "freq",
        "emergency": "emergency",
        "encrypted": "encrypted",
        "system": "sys_num",
        "source_list": "source_list",
    }
}
