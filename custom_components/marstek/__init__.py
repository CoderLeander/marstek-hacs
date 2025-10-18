"""The Marstek Battery integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek Battery from a config entry."""
    _LOGGER.info("Setting up Marstek integration with entry data: %s", entry.data)
    
    # Check if we have all required configuration
    required_keys = ["device_ip", "ble_mac"]
    missing_keys = [key for key in required_keys if key not in entry.data]
    if missing_keys:
        _LOGGER.error("Missing required configuration keys: %s", missing_keys)
        return False
    
    device_ip = entry.data["device_ip"]
    ble_mac = entry.data["ble_mac"]
    remote_port = entry.data.get("remote_port", 30000)
    local_port = entry.data.get("local_port", 30000)
    
    _LOGGER.info("Setting up Marstek device at %s with BLE MAC %s", device_ip, ble_mac)
    
    # Create the UDP client
    client = MarstekUDPClient(
        device_ip=device_ip,
        remote_port=remote_port,
        local_port=local_port
    )
    
    # Test connection
    if not await client.test_connection(ble_mac):
        _LOGGER.error("Failed to connect to Marstek device at %s", device_ip)
        return False
    
    _LOGGER.info("Successfully connected to Marstek device at %s", device_ip)
    
    # Create coordinator for data updates
    coordinator = MarstekDataUpdateCoordinator(hass, client, ble_mac)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    _LOGGER.info("Initial data fetch completed. Data: %s", coordinator.data)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

class MarstekDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Marstek device."""
    
    def __init__(self, hass: HomeAssistant, client: MarstekUDPClient, ble_mac: str):
        """Initialize."""
        self.client = client
        self.ble_mac = ble_mac
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),  # Update every 30 seconds
        )
    
    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get device information
            _LOGGER.info("Updating data for BLE MAC: %s", self.ble_mac)
            data = await self.client.get_device_info(self.ble_mac)
            if data is None:
                _LOGGER.warning("No data received from device")
                raise UpdateFailed("Failed to communicate with device")
            
            _LOGGER.info("Received data: %s", data)
            return data
            
        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err