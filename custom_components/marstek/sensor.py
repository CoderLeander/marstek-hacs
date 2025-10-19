"""Sensor platform for Marstek integration."""
import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

SCAN_INTERVAL = timedelta(minutes=1)

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

# Define sensor descriptions for battery status (common battery metrics)
BATTERY_STATUS_SENSORS = [
    SensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    SensorEntityDescription(
        key="voltage",
        name="Voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    SensorEntityDescription(
        key="current",
        name="Current",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek sensors from config entry."""
    _LOGGER.debug("Setting up Marstek sensors for entry: %s", config_entry.entry_id)
    
    # Get client and device data from hass.data
    integration_data = hass.data[DOMAIN][config_entry.entry_id]
    client = integration_data["client"]
    device_id = config_entry.data.get("device_id")
    
    if device_id is None:
        _LOGGER.error("No device_id found in config entry")
        return
    
    sensors = []
    
    # Create sensors for device information (static data)
    for description in DEVICE_INFO_SENSORS:
        sensor = MarstekDeviceInfoSensor(config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created device info sensor: %s", description.name)
    
    # Create data coordinator for battery status updates
    coordinator = MarstekDataUpdateCoordinator(hass, client, device_id)
    
    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Create sensors for battery status (dynamic data)
    for description in BATTERY_STATUS_SENSORS:
        sensor = MarstekBatteryStatusSensor(coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created battery status sensor: %s", description.name)
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Marstek sensors (%d device info + %d battery status)", 
                 len(sensors), len(DEVICE_INFO_SENSORS), len(BATTERY_STATUS_SENSORS))


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


class MarstekDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Marstek battery data."""

    def __init__(self, hass: HomeAssistant, client, device_id: int):
        """Initialize."""
        self.client = client
        self.device_id = device_id
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            battery_data = await self.client.get_battery_status(self.device_id)
            if battery_data is None:
                raise UpdateFailed("Failed to fetch battery status")
            
            # Extract the result section which contains the actual battery data
            result = battery_data.get("result", {})
            
            _LOGGER.debug("Battery status data: %s", result)
            return result
            
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}")


class MarstekBatteryStatusSensor(SensorEntity):
    """Sensor for Marstek battery status information."""
    
    def __init__(self, coordinator: MarstekDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_battery_{description.key}"
        
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
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        
        # Map sensor key to actual data field in the response
        # This mapping will need to be adjusted based on actual API response
        data_key_mapping = {
            "battery_level": "soc",  # State of charge
            "voltage": "voltage",
            "current": "current", 
            "power": "power",
            "temperature": "temperature",
        }
        
        data_key = data_key_mapping.get(self.entity_description.key)
        if data_key:
            return self.coordinator.data.get(data_key)
        
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await self.coordinator.async_add_listener(self.async_write_ha_state)
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await self.coordinator.async_remove_listener(self.async_write_ha_state)