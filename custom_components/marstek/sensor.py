"""Sensor platform for Marstek integration."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define sensor descriptions for device information
DEVICE_INFO_SENSORS = [
    SensorEntityDescription(
        key="device_name",
        name="Device Name",
        icon="mdi:information",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="device_version",
        name="Device Version",
        icon="mdi:tag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="ble_mac",
        name="BLE MAC Address",
        icon="mdi:bluetooth",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="wifi_mac",
        name="WiFi MAC Address",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="wifi_name",
        name="WiFi Network Name",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="device_reported_ip",
        name="Device IP Address",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek sensors from config entry."""
    _LOGGER.debug("Setting up Marstek sensors for entry: %s", config_entry.entry_id)
    
    # Create sensors for device information
    sensors = []
    
    for description in DEVICE_INFO_SENSORS:
        sensor = MarstekDeviceInfoSensor(config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created sensor: %s", description.name)
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Marstek sensors", len(sensors))


class MarstekDeviceInfoSensor(SensorEntity):
    """Sensor for Marstek device information."""
    
    def __init__(self, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        
        # Get device identifiers for linking
        ble_mac = config_entry.data.get("ble_mac")
        wifi_mac = config_entry.data.get("wifi_mac")
        device_ip = config_entry.data.get("device_ip")
        device_name = config_entry.data.get("device_name", "Marstek Device")
        wifi_name = config_entry.data.get("wifi_name")
        
        # Create device info to link this sensor to the device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ble_mac or wifi_mac or device_ip)},
            manufacturer="Marstek",
            model=device_name,
            name=f"{device_name} ({wifi_name})" if wifi_name else device_name,
            sw_version=str(config_entry.data.get("device_version")) if config_entry.data.get("device_version") else None,
        )
        
        # Set the initial value from config entry data
        self._attr_native_value = config_entry.data.get(description.key)
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._config_entry.data.get(self.entity_description.key)