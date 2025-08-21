# TrunkRecorder Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/ha-trunk-recorder/graphs/commit-activity)

A comprehensive Home Assistant integration for [TrunkRecorder](https://github.com/robotastic/trunk-recorder) that provides real-time police/fire/EMS radio monitoring with a modern, Rdio-Scanner-inspired interface.

## 📻 Features

- **Direct Database Connection** - Connects directly to your TrunkRecorder MySQL/PostgreSQL/SQLite database
- **Real-time Updates** - Live call monitoring with automatic updates
- **Audio Playback** - Stream recorded calls directly from database BLOBs
- **Remote Access** - Full functionality from anywhere via Home Assistant remote access
- **Advanced Filtering** - Filter by system, talkgroup, time, or search terms
- **Statistics Dashboard** - View call counts, top talkgroups, and system activity
- **Emergency Alerts** - Highlights emergency calls for immediate attention
- **Modern UI** - Custom Lovelace card inspired by Rdio-Scanner

## 🎬 Screenshots

<details>
<summary>View Screenshots</summary>

### Live Call Monitor
![Live Calls](screenshots/live_calls.png)

### Call History
![History](screenshots/history.png)

### Statistics Dashboard
![Statistics](screenshots/stats.png)

</details>

## 📋 Prerequisites

- Home Assistant 2024.1.0 or newer
- TrunkRecorder installation with database
- Database access credentials
- Audio stored as BLOBs in the database (or file path access)

## 🚀 Installation

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/yourusername/ha-trunk-recorder`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "TrunkRecorder" and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/tsquared96/ha-trunk-recorder/releases)
2. Extract the `trunk_recorder` folder to your `custom_components` directory:
   ```
   custom_components/
   └── trunk_recorder/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       └── ...
   ```
3. Restart Home Assistant

## ⚙️ Configuration

### Step 1: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **TrunkRecorder**
4. Choose your connection type:
   - **Database** (recommended) - Direct database connection
   - **API** - If you have a TrunkRecorder API server

### Step 2: Database Configuration

For database connection, you'll need:

- **Database Type**: MySQL, PostgreSQL, or SQLite
- **Host**: Database server address (e.g., `localhost` or `192.168.1.100`)
- **Port**: Database port (default: 3306 for MySQL, 5432 for PostgreSQL)
- **Database Name**: Your TrunkRecorder database name (usually `trunk_recorder`)
- **Username**: Database username
- **Password**: Database password

### Step 3: Add the Lovelace Card

1. Install the card resource:
   - Go to **Settings** → **Dashboards** → **Resources**
   - Add Resource:
     - URL: `/local/trunk-recorder-card.js`
     - Type: JavaScript Module

2. Add to your dashboard:
   ```yaml
   type: custom:trunk-recorder-card
   entity: sensor.trunk_recorder_active_calls
   auto_play: true  # Optional: auto-play new calls
   ```

## 🗄️ Database Schema

The integration expects the standard TrunkRecorder database schema:

### Required Tables

- **calls** - Call recordings and metadata
- **systems** - Radio system definitions  
- **talkgroups** - Talkgroup configurations
- **units** - Radio unit IDs (optional)

### Audio Storage

The integration supports audio stored as:
- **BLOB in database** (recommended) - Audio stored directly in the `calls` table
- **File path** - Reference to external audio files (requires file system access)

## 📊 Entities Created

### Sensors
- `sensor.trunk_recorder_active_calls` - Number of active calls
- `sensor.trunk_recorder_total_calls` - Total calls today
- `sensor.trunk_recorder_system_[name]` - Calls per system

### Media Player
- `media_player.trunk_recorder_player` - Audio playback control

## 🎛️ Lovelace Card Features

### Live View
- Real-time active call display
- Emergency call highlighting
- Encrypted call indicators
- One-click audio playback

### History Tab
- Browse past calls
- Search by talkgroup or content
- Time-based filtering
- Pagination support

### Systems Tab
- View all configured systems
- System statistics
- Talkgroup listings

### Statistics Tab
- Call counts and trends
- Top talkgroups
- Total airtime
- Emergency call tracking

## 🔧 Advanced Configuration

### Custom Audio Field Names

If your database uses non-standard field names for audio BLOBs, the integration will automatically try common variations:
- `audio`
- `audio_file`
- `recording`
- `audio_data`
- `wav`
- `mp3`

### Performance Tuning

For large databases, adjust the scan interval in configuration:

```yaml
# In configuration during setup
scan_interval: 30  # seconds
```

### Cache Settings

Audio caching is automatic for files under 10MB. The cache holds up to 50 recent calls.

## 🐛 Troubleshooting

### No Audio Playback
- Verify audio is stored in the database
- Check Home Assistant logs for field name errors
- Ensure database user has SELECT permissions

### Slow Performance
- Increase scan interval
- Add database indexes on `start_time` and `stop_time`
- Consider limiting call history retention

### Connection Issues
- Test database connection with a MySQL/PostgreSQL client
- Verify firewall rules allow database access
- Check database user permissions

## 📝 Development

### Project Structure
```
custom_components/trunk_recorder/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── config_flow.py        # Configuration UI
├── const.py             # Constants and field mappings
├── coordinator.py       # Data update coordinator
├── database_client.py
