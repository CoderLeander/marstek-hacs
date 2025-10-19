"""Config flow for Marstek integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("device_ip"): cv.string,
    vol.Optional("remote_port", default=30000): cv.port,
    vol.Optional("local_port", default=30000): cv.port,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user step."""
        errors = {}
        
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors
            )

        device_ip = user_input["device_ip"]
        remote_port = user_input.get("remote_port", 30000)
        local_port = user_input.get("local_port", 30000)

        # Check if this device is already configured
        await self.async_set_unique_id(device_ip)
        self._abort_if_unique_id_configured()

        _LOGGER.debug("Testing connection to Marstek device at %s:%s", device_ip, remote_port)

        try:
            # Create MarstekUDPClient instance
            client = MarstekUDPClient(device_ip, remote_port, local_port)

            # Use string "0" to request discovery of all batteries on the network
            if not await client.test_connection("0"):
                errors["base"] = "cannot_connect"
                _LOGGER.warning("Failed to connect to Marstek device at %s:%s", device_ip, remote_port)
            
        except Exception as exc:
            _LOGGER.exception("Unexpected error connecting to Marstek device: %s", exc)
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors
            )
        
        entry_data = {
            "device_ip": device_ip,
            "remote_port": remote_port,
            "local_port": local_port,
        }

        _LOGGER.info("Successfully configured Marstek device at %s:%s", device_ip, remote_port)

        return self.async_create_entry(
            title=f"Marstek ({device_ip})",
            data=entry_data
        )