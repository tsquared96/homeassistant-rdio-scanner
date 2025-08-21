"""Config flow for Rdio-Scanner integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PATH
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_NAME, DEFAULT_PATH, DOMAIN
from .rdio_db import RdioScannerDB

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    db_path = os.path.join(data[CONF_PATH], "rdio-scanner.db")
    
    if not os.path.exists(db_path):
        raise CannotConnect(f"Database not found at {db_path}")
    
    # Test connection
    try:
        db = RdioScannerDB(data)
        await db.connect()
        systems = await db.get_systems()
        await db.close()
        
        title = data.get(CONF_NAME, DEFAULT_NAME)
        if systems:
            title = f"{title} ({len(systems)} systems)"
        
        return {"title": title}
    except Exception as err:
        _LOGGER.error("Cannot connect to database: %s", err)
        raise CannotConnect(f"Database connection failed: {err}")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rdio-Scanner."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect as err:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Cannot connect: %s", err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_PATH, default=DEFAULT_PATH): str,
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "default_path": DEFAULT_PATH,
            },
        )
