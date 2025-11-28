"""Select platform for Marstek integration."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek select entities."""
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    rpc_id = hass.data[DOMAIN][entry.entry_id]["rpc_id"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]

    entities = []
    
    # Create a mode select entity for each device
    for ble_mac, device_info in devices.items():
        entities.append(MarstekModeSelect(client, rpc_id, device_info, entry))
    
    async_add_entities(entities)


class MarstekModeSelect(SelectEntity):
    """Representation of a Marstek mode selector."""

    _attr_options = ["Auto", "Manual"]
    _attr_icon = "mdi:tune"

    def __init__(self, client, rpc_id, device_info, entry):
        """Initialize the select entity."""
        self._client = client
        self._rpc_id = rpc_id
        self._device_info = device_info
        self._entry = entry
        
        ble_mac = device_info.get("ble_mac") or device_info.get("mac")
        device_name = device_info.get("device", "Marstek")
        
        self._attr_name = f"Mode"
        self._attr_unique_id = f"{ble_mac}_mode_select"
        self._attr_current_option = None
        
        # Set up device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ble_mac)},
            name=device_name,
            manufacturer="Marstek",
            model=device_info.get("device"),
            sw_version=str(device_info.get("ver")) if device_info.get("ver") else None,
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected mode."""
        _LOGGER.info("Setting mode to %s for device %s", option, self._rpc_id)
        
        try:
            if option == "Auto":
                response = await self._client.set_auto_mode(self._rpc_id)
            elif option == "Manual":
                response = await self._client.set_manual_mode(self._rpc_id)
            else:
                _LOGGER.error("Unknown mode: %s", option)
                return
            
            if response:
                self._attr_current_option = option
                self.async_write_ha_state()
                _LOGGER.info("Mode changed to %s successfully", option)
                
                # Poll once after setting to confirm
                try:
                    verify_response = await self._client.get_mode_status(self._rpc_id)
                    if verify_response and "result" in verify_response:
                        current_mode = verify_response["result"].get("mode")
                        if current_mode in self._attr_options:
                            self._attr_current_option = current_mode
                            self.async_write_ha_state()
                            _LOGGER.debug("Verified mode is now: %s", current_mode)
                except Exception as verify_exc:
                    _LOGGER.debug("Could not verify mode after setting: %s", verify_exc)
            else:
                _LOGGER.error("Failed to change mode to %s", option)
        except Exception as exc:
            _LOGGER.error("Error changing mode to %s: %s", option, exc)
