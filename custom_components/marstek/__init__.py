"""Simple Marstek integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek integration - send Marstek.GetDevice once."""
    _LOGGER.info("Setting up Marstek integration")
    
    device_ip = entry.data["device_ip"]
    ble_mac = entry.data["ble_mac"]
    remote_port = entry.data.get("remote_port", 30000)
    local_port = entry.data.get("local_port", 30000)
    
    # Create client and send command once
    client = MarstekUDPClient(device_ip, remote_port, local_port)
    result = await client.get_device_info(ble_mac)
    
    if result is None:
        _LOGGER.error("Failed to get device info")
        return False
    
    _LOGGER.info("Setup complete - device responded")
    
    # Store minimal data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "data": result}
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True