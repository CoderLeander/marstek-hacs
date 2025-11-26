"""Number platform for Marstek integration."""
import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek number entities."""
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    rpc_id = hass.data[DOMAIN][entry.entry_id]["rpc_id"]
    
    # Get the mode coordinator from sensor platform
    # We need to access the coordinator to check current mode
    entities = []
    entities.append(MarstekManualPowerNumber(client, rpc_id, entry, hass))
    
    async_add_entities(entities)


class MarstekManualPowerNumber(NumberEntity):
    """Representation of Marstek Manual Mode Power Control."""

    _attr_icon = "mdi:lightning-bolt"
    _attr_native_min_value = -1000
    _attr_native_max_value = 1000
    _attr_native_step = 100
    _attr_native_unit_of_measurement = "W"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, client, rpc_id, entry, hass):
        """Initialize the number entity."""
        self._client = client
        self._rpc_id = rpc_id
        self._entry = entry
        self._hass = hass
        
        ble_mac = entry.data.get("ble_mac")
        wifi_mac = entry.data.get("wifi_mac")
        device_ip = entry.data.get("device_ip")
        device_name = entry.data.get("device_name", "Marstek Device")
        wifi_name = entry.data.get("wifi_name")
        
        self._attr_name = f"{device_name} Manual Power"
        self._attr_unique_id = f"{ble_mac or wifi_mac or device_ip}_manual_power"
        self._attr_native_value = 0  # Default to 0W
        self._current_mode = None
        
        # Set up device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ble_mac or wifi_mac or device_ip)},
            name=f"{device_name} ({wifi_name})" if wifi_name else device_name,
            manufacturer="Marstek",
            model=device_name,
            sw_version=str(entry.data.get("device_version")) if entry.data.get("device_version") else None,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available - only available in Manual mode."""
        return self._current_mode == "Manual"

    async def async_set_native_value(self, value: float) -> None:
        """Update the power setting for manual mode."""
        power_value = int(value)
        _LOGGER.info("Setting manual mode power to %dW for device %s", power_value, self._rpc_id)
        
        try:
            # Always use time slot 1 with default schedule (all week, 08:30-20:30)
            response = await self._client.set_manual_power(
                device_id=self._rpc_id,
                power=power_value,
                time_num=1,
                start_time="08:30",
                end_time="20:30",
                week_set=127  # All days (Mon-Sun)
            )
            
            if response:
                self._attr_native_value = power_value
                self.async_write_ha_state()
                _LOGGER.info("Manual power set to %dW successfully", power_value)
            else:
                _LOGGER.error("Failed to set manual power to %dW", power_value)
        except Exception as exc:
            _LOGGER.error("Error setting manual power to %dW: %s", power_value, exc)

    async def async_update(self) -> None:
        """Fetch the current mode and power from the device."""
        try:
            response = await self._client.get_mode_status(self._rpc_id)
            if response and "result" in response:
                result = response["result"]
                self._current_mode = result.get("mode")
                
                # If in Manual mode, try to get the current power setting
                if self._current_mode == "Manual" and "manual_cfg" in result:
                    manual_cfg = result["manual_cfg"]
                    if isinstance(manual_cfg, dict):
                        power = manual_cfg.get("power")
                        if power is not None:
                            self._attr_native_value = int(power)
                    elif isinstance(manual_cfg, list) and len(manual_cfg) > 0:
                        # If manual_cfg is a list, get power from first time slot
                        power = manual_cfg[0].get("power")
                        if power is not None:
                            self._attr_native_value = int(power)
        except Exception as exc:
            _LOGGER.error("Error fetching manual power status: %s", exc)
