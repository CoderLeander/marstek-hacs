"""Config flow for Marstek Battery integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_DEVICE_IP,
    CONF_BLE_MAC,
    CONF_REMOTE_PORT,
    CONF_LOCAL_PORT,
    DEFAULT_REMOTE_PORT,
    DEFAULT_LOCAL_PORT,
)
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IP): str,
        vol.Required(CONF_BLE_MAC): str,
        vol.Optional(CONF_REMOTE_PORT, default=DEFAULT_REMOTE_PORT): int,
        vol.Optional(CONF_LOCAL_PORT, default=DEFAULT_LOCAL_PORT): int,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = MarstekUDPClient(
        device_ip=data[CONF_DEVICE_IP],
        remote_port=data[CONF_REMOTE_PORT], 
        local_port=data[CONF_LOCAL_PORT],
    )
    
    # Test the connection
    if not await client.test_connection(data[CONF_BLE_MAC]):
        raise CannotConnect
    
    # Return info that you want to store in the config entry.
    return {"title": f"Marstek Battery ({data[CONF_DEVICE_IP]})"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marstek Battery."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""