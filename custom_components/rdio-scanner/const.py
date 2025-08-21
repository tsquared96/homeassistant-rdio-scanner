"""Constants for the Rdio-Scanner integration."""

DOMAIN = "rdio_scanner"

# Configuration constants
DEFAULT_NAME = "Rdio-Scanner"
DEFAULT_PATH = "/opt/rdio-scanner/data"

# Rdio-Scanner database schema
# Based on the database structure we explored in your webapp
RDIO_TABLES = {
    "calls": "rdio_scanner_calls",
    "systems": "rdio_scanner_systems", 
    "talkgroups": "rdio_scanner_talkgroups",
}

# Audio format in database
AUDIO_MIME_TYPE = "audio/mpeg"  # MP3 format after conversion
