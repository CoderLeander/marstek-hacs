"""Simple config flow for Marstek."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("device_ip"): str,
    vol.Required("ble_mac"): str,
    vol.Optional("remote_port", default=30000): int,
    vol.Optional("local_port", default=30000): int,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Simple config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        # Test connection
        client = MarstekUDPClient(
            user_input["device_ip"],
            user_input["remote_port"],
            user_input["local_port"]
        )
        
        if not await client.test_connection(user_input["ble_mac"]):
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "cannot_connect"}
            )

        return self.async_create_entry(
            title=f"Marstek ({user_input['device_ip']})",
            data=user_input
        )