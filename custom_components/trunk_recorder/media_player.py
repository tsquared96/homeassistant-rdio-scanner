```python
"""Media player platform for TrunkRecorder."""
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrunkRecorderCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrunkRecorder media player."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([TrunkRecorderMediaPlayer(coordinator)])


class TrunkRecorderMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media player for TrunkRecorder calls."""
    
    def __init__(self, coordinator: TrunkRecorderCoordinator) -> None:
        """Initialize media player."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_player"
        self._attr_name = "Trunk Recorder Player"
        self._attr_icon = "mdi:radio"
        self._attr_media_content_type = MediaType.MUSIC
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
        )
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
            tg_name = self._current_call.get("talkgroup_name", "Unknown")
            return f"{tg_name}"
        return None
    
    @property
    def media_artist(self):
        """Return the artist of current media."""
        if self._current_call:
            return self._current_call.get("system_name", "Unknown System")
        return None
    
    @property
    def media_content_id(self):
        """Return the content ID of current media."""
        if self._current_call:
            return self._current_call.get("id")
        return None
    
    async def async_play_media(self, media_type: str, media_id: str, **kwargs):
        """Play a specific call."""
        # Find the call in history or active calls
        call = None
        if media_id in self.coordinator.active_calls:
            call = self.coordinator.active_calls[media_id]
        else:
            for historical_call in self.coordinator.call_history:
                if historical_call.get("id") == media_id:
                    call = historical_call
                    break
        
        if call:
            self._current_call = call
            self._state = MediaPlayerState.PLAYING
            self.async_write_ha_state()
    
    async def async_media_play(self):
        """Play media."""
        self._state = MediaPlayerState.PLAYING
        self.async_write_ha_state()
    
    async def async_media_pause(self):
        """Pause media."""
        self._state = MediaPlayerState.PAUSED
        self.async_write_ha_state()
    
    async def async_media_stop(self):
        """Stop media."""
        self._state = MediaPlayerState.IDLE
        self._current_call = None
        self.async_write_ha_state()
```

## 8. Lovelace Card (www/trunk-recorder-card.js)
```javascript
class TrunkRecorderCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.activeCall = null;
    this.callHistory = [];
    this.systems = [];
    this.selectedSystem = null;
    this.selectedTalkgroup = null;
    this.audioPlayer = null;
    this.websocket = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
    this.entity = config.entity;
  }

  set hass(hass) {
    this._hass = hass;
    
    if (!this.initialized) {
      this.initialized = true;
      this.setupWebSocket();
      this.render();
      this.setupEventListeners();
    }
    
    this.updateData();
  }

  setupWebSocket() {
    // Connect to Home Assistant WebSocket for real-time updates
    this._hass.connection.subscribeEvents((event) => {
      if (event.event_type === 'trunk_recorder_call_start') {
        this.handleNewCall(event.data);
      } else if (event.event_type === 'trunk_recorder_call_end') {
        this.handleCallEnd(event.data);
      }
    });
  }

  handleNewCall(callData) {
    this.activeCall = callData;
    this.updateActiveCallDisplay();
    
    // Auto-play if enabled
    if (this.config.auto_play) {
      this.playCall(callData);
    }
  }

  handleCallEnd(callData) {
    if (this.activeCall && this.activeCall.id === callData.id) {
      this.activeCall = null;
      this.updateActiveCallDisplay();
    }
    
    // Add to history
    this.callHistory.unshift(callData);
    if (this.callHistory.length > 100) {
      this.callHistory = this.callHistory.slice(0, 100);
    }
    this.updateHistoryDisplay();
  }

  async playCall(call) {
    const audioUrl = `/api/trunk_recorder/audio/${call.id}`;
    
    if (!this.audioPlayer) {
      this.audioPlayer = this.shadowRoot.querySelector('#audio-player');
    }
    
    this.audioPlayer.src = audioUrl;
    this.audioPlayer.play();
    
    // Update UI
    this.shadowRoot.querySelector('#now-playing').textContent = 
      `${call.talkgroup_name} - ${call.system_name}`;
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          background: var(--card-background-color);
          border-radius: var(--ha-card-border-radius);
          box-shadow: var(--ha-card-box-shadow);
        }
        
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .title {
          font-size: 20px;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .status {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: var(--error-color);
          animation: pulse 2s infinite;
        }
        
        .status-indicator.active {
          background: var(--success-color);
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        .tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
          border-bottom: 1px solid var(--divider-color);
        }
        
        .tab {
          padding: 8px 16px;
          cursor: pointer;
          color: var(--secondary-text-color);
          border-bottom: 2px solid transparent;
          transition: all 0.3s;
        }
        
        .tab.active {
          color: var(--primary-color);
          border-bottom-color: var(--primary-color);
        }
        
        .content {
          min-height: 400px;
        }
        
        .active-call {
          padding: 16px;
          background: var(--primary-color);
          color: white;
          border-radius: 8px;
          margin-bottom: 16px;
        }
        
        .call-info {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          margin-top: 8px;
        }
        
        .call-item {
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 4px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: background 0.3s;
        }
        
        .call-item:hover {
          background: var(--primary-color-light);
        }
        
        .call-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        
        .call-talkgroup {
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .call-time {
          color: var(--secondary-text-color);
          font-size: 12px;
        }
        
        .call-details {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        
        .filters {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }
        
        select {
          padding: 8px;
          border-radius: 4px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          color: var(--primary-text-color);
        }
        
        .audio-controls {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          margin-top: 16px;
        }
        
        .play-button {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: var(--primary-color);
          color: white;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .play-button:hover {
          background: var(--primary-color-dark);
        }
        
        #audio-player {
          flex: 1;
        }
        
        .frequency-display {
          font-family: monospace;
          color: var(--primary-color);
        }
        
        .emergency {
          color: var(--error-color);
          font-weight: bold;
        }
        
        .encrypted {
          color: var(--warning-color);
        }
      </style>
      
      <div class="header">
        <div class="title">Trunk Recorder</div>
        <div class="status">
          <span id="status-text">Idle</span>
          <div class="status-indicator" id="status-indicator"></div>
        </div>
      </div>
      
      <div class="tabs">
        <div class="tab active" data-tab="live">Live</div>
        <div class="tab" data-tab="history">History</div>
        <div class="tab" data-tab="systems">Systems</div>
        <div class="tab" data-tab="stats">Statistics</div>
      </div>
      
      <div class="filters">
        <select id="system-filter">
          <option value="">All Systems</option>
        </select>
        <select id="talkgroup-filter">
          <option value="">All Talkgroups</option>
        </select>
        <input type="text" id="search" placeholder="Search calls..." />
      </div>
      
      <div class="content" id="content">
        <div id="live-content">
          <div id="active-call-container"></div>
          <div id="recent-calls"></div>
        </div>
        
        <div id="history-content" style="display: none;">
          <div id="call-history"></div>
        </div>
        
        <div id="systems-content" style="display: none;">
          <div id="systems-list"></div>
        </div>
        
        <div id="stats-content" style="display: none;">
          <div id="statistics"></div>
        </div>
      </div>
      
      <div class="audio-controls">
        <button class="play-button" id="play-button">
          <ha-icon icon="mdi:play"></ha-icon>
        </button>
        <audio id="audio-player" controls></audio>
        <div id="now-playing">No call selected</div>
      </div>
    `;
  }

  setupEventListeners() {
    // Tab switching
    this.shadowRoot.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        this.switchTab(tab.dataset.tab);
      });
    });
    
    // Filter changes
    this.shadowRoot.querySelector('#system-filter').addEventListener('change', () => {
      this.applyFilters();
    });
    
    this.shadowRoot.querySelector('#talkgroup-filter').addEventListener('change', () => {
      this.applyFilters();
    });
    
    // Search
    this.shadowRoot.querySelector('#search').addEventListener('input', (e) => {
      this.searchCalls(e.target.value);
    });
    
    // Play button
    this.shadowRoot.querySelector('#play-button').addEventListener('click', () => {
      this.togglePlayback();
    });
  }

  switchTab(tabName) {
    // Update tab UI
    this.shadowRoot.querySelectorAll('.tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content
    ['live', 'history', 'systems', 'stats'].forEach(content => {
      const element = this.shadowRoot.querySelector(`#${content}-content`);
      if (element) {
        element.style.display = content === tabName ? 'block' : 'none';
      }
    });
    
    // Load content for tab
    switch(tabName) {
      case 'history':
        this.loadHistory();
        break;
      case 'systems':
        this.loadSystems();
        break;
      case 'stats':
        this.loadStatistics();
        break;
    }
  }

  async updateData() {
    const state = this._hass.states[this.entity];
    if (!state) return;
    
    // Update active calls
    if (state.attributes.calls) {
      this.updateActiveCalls(state.attributes.calls);
    }
    
    // Update systems
    await this.loadSystemsData();
  }

  updateActiveCalls(calls) {
    const container = this.shadowRoot.querySelector('#recent-calls');
    if (!container) return;
    
    container.innerHTML = calls.map(call => `
      <div class="call-item" data-call-id="${call.id}">
        <div class="call-header">
          <span class="call-talkgroup">${call.talkgroup_name || 'Unknown'}</span>
          <span class="call-time">${this.formatTime(call.start_time)}</span>
        </div>
        <div class="call-details">
          <span class="frequency-display">${call.frequency} MHz</span>
          <span>${call.system_name}</span>
          ${call.emergency ? '<span class="emergency">EMERGENCY</span>' : ''}
          ${call.encrypted ? '<span class="encrypted">ENCRYPTED</span>' : ''}
        </div>
      </div>
    `).join('');
    
    // Add click handlers
    container.querySelectorAll('.call-item').forEach(item => {
      item.addEventListener('click', () => {
        const callId = item.dataset.callId;
        const call = calls.find(c => c.id === callId);
        if (call) this.playCall(call);
      });
    });
  }

  updateActiveCallDisplay() {
    const container = this.shadowRoot.querySelector('#active-call-container');
    const statusText = this.shadowRoot.querySelector('#status-text');
    const statusIndicator = this.shadowRoot.querySelector('#status-indicator');
    
    if (this.activeCall) {
      statusText.textContent = 'Active Call';
      statusIndicator.classList.add('active');
      
      container.innerHTML = `
        <div class="active-call">
          <h3>${this.activeCall.talkgroup_name || 'Unknown Talkgroup'}</h3>
          <div class="call-info">
            <div>System: ${this.activeCall.system_name}</div>
            <div>Frequency: ${this.activeCall.frequency} MHz</div>
            <div>Units: ${(this.activeCall.units || []).join(', ')}</div>
            <div>Duration: <span id="call-duration">0:00</span></div>
          </div>
        </div>
      `;
      
      // Update duration
      this.updateCallDuration();
    } else {
      statusText.textContent = 'Idle';
      statusIndicator.classList.remove('active');
      container.innerHTML = '';
    }
  }

  updateCallDuration() {
    if (!this.activeCall) return;
    
    const startTime = new Date(this.activeCall.start_time);
    const now = new Date();
    const duration = Math.floor((now - startTime) / 1000);
    
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    
    const durationElement = this.shadowRoot.querySelector('#call-duration');
    if (durationElement) {
      durationElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    
    // Update every second
    setTimeout(() => this.updateCallDuration(), 1000);
  }

  async loadHistory() {
    // Call Home Assistant service to get call history
    const history = await this._hass.callService('trunk_recorder', 'get_history', {
      limit: 100
    });
    
    const container = this.shadowRoot.querySelector('#call-history');
    container.innerHTML = this.renderCallList(history);
  }

  async loadSystems() {
    const systems = await this._hass.callService('trunk_recorder', 'get_systems', {});
    
    const container = this.shadowRoot.querySelector('#systems-list');
    container.innerHTML = systems.map(system => `
      <div class="system-card">
        <h3>${system.name}</h3>
        <div>ID: ${system.id}</div>
        <div>Type: ${system.type}</div>
        <div>Talkgroups: ${system.talkgroup_count}</div>
      </div>
    `).join('');
  }

  async loadStatistics() {
    const stats = await this._hass.callService('trunk_recorder', 'get_statistics', {});
    
    const container = this.shadowRoot.querySelector('#statistics');
    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">${stats.total_calls_today}</div>
          <div class="stat-label">Calls Today</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.active_systems}</div>
          <div class="stat-label">Active Systems</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.total_talkgroups}</div>
          <div class="stat-label">Talkgroups</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${this.formatDuration(stats.total_airtime)}</div>
          <div class="stat-label">Total Airtime</div>
        </div>
      </div>
    `;
  }

  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }

  formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }

  applyFilters() {
    // Implementation for filtering calls
  }

  searchCalls(query) {
    // Implementation for searching calls
  }

  togglePlayback() {
    const player = this.shadowRoot.querySelector('#audio-player');
    const button = this.shadowRoot.querySelector('#play-button');
    const icon = button.querySelector('ha-icon');
    
    if (player.paused) {
      player.play();
      icon.setAttribute('icon', 'mdi:pause');
    } else {
      player.pause();
      icon.setAttribute('icon', 'mdi:play');
    }
  }

  getCardSize() {
    return 4;
  }
}

customElements.define('trunk-recorder-card', TrunkRecorderCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'trunk-recorder-card',
  name: 'Trunk Recorder Card',
  preview: false,
  description: 'A card for displaying TrunkRecorder scanner feeds'
});
