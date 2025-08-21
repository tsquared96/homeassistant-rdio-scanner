"""Config flow for Trunk Recorder integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_DB_NAME,
    CONF_DB_TYPE,
    DEFAULT_DB_NAME,
    DEFAULT_NAME,
    DEFAULT_PORT_MYSQL,
    DEFAULT_PORT_POSTGRES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # TODO: Add actual database connection test here
    # For now, just return success
    
    return {"title": data.get(CONF_NAME, DEFAULT_NAME)}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trunk Recorder."""
    
    VERSION = 1
    
    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}
        self._db_type: str = "mysql"
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_DB_TYPE, default="mysql"): vol.In(
                            ["mysql", "postgresql", "sqlite"]
                        ),
                    }
                ),
            )
        
        self._db_type = user_input[CONF_DB_TYPE]
        return await self.async_step_database()
    
    async def async_step_database(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle database configuration."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Store all configuration
                self._data.update(user_input)
                self._data[CONF_DB_TYPE] = self._db_type
                
                info = await validate_input(self.hass, self._data)
                
                return self.async_create_entry(title=info["title"], data=self._data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        # Set default port based on database type
        default_port = DEFAULT_PORT_MYSQL
        if self._db_type == "postgresql":
            default_port = DEFAULT_PORT_POSTGRES
        elif self._db_type == "sqlite":
            default_port = None
        
        # Different schema based on database type
        if self._db_type == "sqlite":
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST, default="/var/lib/trunk-recorder"): str,
                    vol.Required(CONF_DB_NAME, default="trunk_recorder.db"): str,
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST, default="localhost"): str,
                    vol.Required(CONF_PORT, default=default_port): int,
                    vol.Required(CONF_DB_NAME, default=DEFAULT_DB_NAME): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            )
        
        return self.async_show_form(
            step_id="database",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "db_type": self._db_type.upper(),
            },
        )
