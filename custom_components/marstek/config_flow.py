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
    vol.Optional("remote_port", default=30000): int,
    vol.Optional("local_port", default=30000): int,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle user step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        # Use provided device_ip and ble_mac=0 to scan for all devices
        device_ip = user_input["device_ip"]
        remote_port = user_input.get("remote_port", 30000)
        local_port = user_input.get("local_port", 30000)

        client = MarstekUDPClient(device_ip, remote_port, local_port)

        # Use numeric 0 to request discovery of all batteries on the network
        if not await client.test_connection(0):
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "cannot_connect"}
            )

        entry_data = {
            "device_ip": device_ip,
            "remote_port": remote_port,
            "local_port": local_port,
        }

        return self.async_create_entry(
            title=f"Marstek ({device_ip})",
            data=entry_data
        )