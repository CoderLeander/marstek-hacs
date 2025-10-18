"""Support for Marstek Battery sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek Battery sensor platform."""
    _LOGGER.info("Setting up Marstek sensor platform")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create sensors based on available data
    entities = []
    for sensor_type, config in SENSOR_TYPES.items():
        _LOGGER.info("Creating sensor: %s", sensor_type)
        entities.append(
            MarstekSensor(
                coordinator,
                config_entry,
                sensor_type,
                config,
            )
        )
    
    _LOGGER.info("Adding %d sensor entities", len(entities))
    async_add_entities(entities)

class MarstekSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Marstek Battery sensor."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        sensor_config: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config
        self._attr_name = f"Marstek {sensor_config['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")
        
        # Set device class if available
        if "device_class" in sensor_config:
            device_class_name = sensor_config["device_class"]
            if hasattr(SensorDeviceClass, device_class_name.upper()):
                self._attr_device_class = getattr(SensorDeviceClass, device_class_name.upper())
        
        # Set state class if available  
        if "state_class" in sensor_config:
            state_class_name = sensor_config["state_class"]
            if hasattr(SensorStateClass, state_class_name.upper()):
                self._attr_state_class = getattr(SensorStateClass, state_class_name.upper())
    
    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Marstek Battery",
            "manufacturer": "Marstek",
            "model": "Battery System",
            "sw_version": "1.0.0",
        }
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available for %s", self._sensor_type)
            return None
        
        # Extract the sensor value from the coordinator data
        # This will need to be adapted based on your actual API response structure
        data = self.coordinator.data
        _LOGGER.debug("Processing sensor %s with data: %s", self._sensor_type, data)
        
        # Example mapping - you'll need to adjust based on your actual API response
        value = None
        if self._sensor_type == "battery_voltage":
            # Look for voltage in the response data
            value = self._extract_value(data, ["voltage", "volt", "v"])
        elif self._sensor_type == "battery_current":
            # Look for current in the response data
            value = self._extract_value(data, ["current", "amp", "a"])
        elif self._sensor_type == "battery_power":
            # Look for power in the response data
            value = self._extract_value(data, ["power", "watt", "w"])
        elif self._sensor_type == "battery_temperature":
            # Look for temperature in the response data
            value = self._extract_value(data, ["temperature", "temp", "t"])
        elif self._sensor_type == "battery_soc":
            # Look for state of charge in the response data
            value = self._extract_value(data, ["soc", "state_of_charge", "battery_level", "charge"])
        
        _LOGGER.debug("Sensor %s extracted value: %s", self._sensor_type, value)
        return value
    
    def _extract_value(self, data: dict, possible_keys: list[str]) -> Any:
        """Extract value from data using possible key names."""
        if not isinstance(data, dict):
            return None
        
        # Try to find the value in nested structures
        def search_nested(obj, keys):
            if isinstance(obj, dict):
                # First try direct key matches
                for key in keys:
                    if key in obj:
                        return obj[key]
                    # Also try case-insensitive matching
                    for obj_key, obj_value in obj.items():
                        if obj_key.lower() == key.lower():
                            return obj_value
                
                # If not found, search recursively
                for value in obj.values():
                    result = search_nested(value, keys)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_nested(item, keys)
                    if result is not None:
                        return result
            return None
        
        return search_nested(data, possible_keys)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success