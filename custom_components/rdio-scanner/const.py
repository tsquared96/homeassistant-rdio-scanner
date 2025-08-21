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
```

## 5. rdio_db.py
```python
"""Database interface for Rdio-Scanner."""
import base64
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiosqlite
from homeassistant.const import CONF_PATH

from .const import RDIO_TABLES

_LOGGER = logging.getLogger(__name__)


class RdioScannerDB:
    """Interface to Rdio-Scanner SQLite database."""
    
    def __init__(self, config: dict) -> None:
        """Initialize database connection."""
        self.db_path = os.path.join(config[CONF_PATH], "rdio-scanner.db")
        self.conn = None
        self._audio_cache = {}
    
    async def connect(self) -> None:
        """Connect to database."""
        if not self.conn:
            self.conn = await aiosqlite.connect(self.db_path)
            # Enable row factory for dict-like access
            self.conn.row_factory = aiosqlite.Row
    
    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
    
    async def get_recent_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent calls from database."""
        await self.connect()
        
        query = """
            SELECT 
                id,
                dateTime,
                system,
                talkgroup,
                frequency,
                frequencies,
                patches,
                sources,
                len as call_length,
                talkgroupData
            FROM rdio_scanner_calls
            ORDER BY dateTime DESC
            LIMIT ?
        """
        
        cursor = await self.conn.execute(query, (limit,))
        rows = await cursor.fetchall()
        
        calls = []
        for row in rows:
            call = dict(row)
            
            # Parse JSON fields
            if call.get('frequencies'):
                try:
                    call['frequencies'] = json.loads(call['frequencies'])
                except:
                    call['frequencies'] = []
            
            if call.get('patches'):
                try:
                    call['patches'] = json.loads(call['patches'])
                except:
                    call['patches'] = []
            
            if call.get('sources'):
                try:
                    call['sources'] = json.loads(call['sources'])
                except:
                    call['sources'] = []
            
            if call.get('talkgroupData'):
                try:
                    tg_data = json.loads(call['talkgroupData'])
                    call['talkgroup_name'] = tg_data.get('label', f"TG {call['talkgroup']}")
                    call['talkgroup_tag'] = tg_data.get('tag', '')
                    call['talkgroup_group'] = tg_data.get('group', '')
                except:
                    call['talkgroup_name'] = f"TG {call['talkgroup']}"
            
            # Convert timestamp to readable format
            if call.get('dateTime'):
                call['timestamp'] = datetime.fromtimestamp(call['dateTime'] / 1000).isoformat()
            
            calls.append(call)
        
        return calls
    
    async def get_call_audio(self, call_id: int) -> Optional[Dict[str, Any]]:
        """Get audio data for a specific call."""
        # Check cache first
        if call_id in self._audio_cache:
            return self._audio_cache[call_id]
        
        await self.connect()
        
        query = """
            SELECT audio, audioName, audioType
            FROM rdio_scanner_calls
            WHERE id = ?
        """
        
        cursor = await self.conn.execute(query, (call_id,))
        row = await cursor.fetchone()
        
        if row and row['audio']:
            audio_data = {
                'data': row['audio'],  # This is the BLOB
                'type': row['audioType'] or 'audio/mpeg',
                'name': row['audioName'] or f'call_{call_id}.mp3',
            }
            
            # Cache if not too large (< 10MB)
            if len(row['audio']) < 10 * 1024 * 1024:
                self._audio_cache[call_id] = audio_data
                
                # Limit cache size
                if len(self._audio_cache) > 50:
                    self._audio_cache.pop(next(iter(self._audio_cache)))
            
            return audio_data
        
        return None
    
    async def get_systems(self) -> List[Dict[str, Any]]:
        """Get all systems from database."""
        await self.connect()
        
        query = """
            SELECT DISTINCT system
            FROM rdio_scanner_calls
            WHERE system IS NOT NULL
            ORDER BY system
        """
        
        cursor = await self.conn.execute(query)
        rows = await cursor.fetchall()
        
        systems = []
        for row in rows:
            systems.append({
                'id': row['system'],
                'name': f"System {row['system']}",
            })
        
        return systems
    
    async def get_talkgroups(self, system_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get unique talkgroups from calls."""
        await self.connect()
        
        where_clause = "WHERE system = ?" if system_id else ""
        params = [system_id] if system_id else []
        
        query = f"""
            SELECT DISTINCT 
                talkgroup,
                talkgroupData
            FROM rdio_scanner_calls
            {where_clause}
            ORDER BY talkgroup
        """
        
        cursor = await self.conn.execute(query, params)
        rows = await cursor.fetchall()
        
        talkgroups = []
        for row in rows:
            tg = {
                'id': row['talkgroup'],
                'name': f"TG {row['talkgroup']}",
            }
            
            if row['talkgroupData']:
                try:
                    tg_data = json.loads(row['talkgroupData'])
                    tg['name'] = tg_data.get('label', tg['name'])
                    tg['tag'] = tg_data.get('tag', '')
                    tg['group'] = tg_data.get('group', '')
                except:
                    pass
            
            talkgroups.append(tg)
        
        return talkgroups
    
    async def get_call_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get call statistics."""
        await self.connect()
        
        # Calculate timestamp for X hours ago
        since = datetime.now() - timedelta(hours=hours)
        since_ms = int(since.timestamp() * 1000)
        
        query = """
            SELECT 
                COUNT(*) as total_calls,
                COUNT(DISTINCT system) as systems,
                COUNT(DISTINCT talkgroup) as talkgroups,
                AVG(len) as avg_length,
                MAX(len) as max_length
            FROM rdio_scanner_calls
            WHERE dateTime > ?
        """
        
        cursor = await self.conn.execute(query, (since_ms,))
        row = await cursor.fetchone()
        
        return dict(row) if row else {}
