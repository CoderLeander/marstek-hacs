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

# Define sensor descriptions for battery status (based on actual Bat.GetStatus response)
BATTERY_STATUS_SENSORS = [
    SensorEntityDescription(
        key="soc",
        name="State of Charge",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    SensorEntityDescription(
        key="bat_temp",
        name="Battery Temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="bat_capacity",
        name="Battery Capacity",
        native_unit_of_measurement="Wh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-capacity-variant",
    ),
    SensorEntityDescription(
        key="rated_capacity",
        name="Rated Capacity",
        native_unit_of_measurement="Wh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-capacity-outline",
    ),
    SensorEntityDescription(
        key="error_code",
        name="Error Code",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]

# Define sensor descriptions for mode status (from ES.GetMode response)
MODE_STATUS_SENSORS = [
    SensorEntityDescription(
        key="mode",
        name="Operating Mode",
        icon="mdi:cog",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="ongrid_power",
        name="On-Grid Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    SensorEntityDescription(
        key="offgrid_power", 
        name="Off-Grid Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:power-plug-off",
    ),
    SensorEntityDescription(
        key="bat_soc_mode",
        name="Battery SOC (Mode)",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-outline",
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
    try:
        integration_data = hass.data[DOMAIN][config_entry.entry_id]
        client = integration_data["client"]
    except KeyError:
        _LOGGER.error("Integration data not found for entry %s", config_entry.entry_id)
        return
    
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
    
    # Perform initial data fetch (but don't fail if it doesn't work immediately)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.warning("Initial battery data fetch failed, will retry later: %s", exc)
        # Don't fail setup, just continue without initial data
        # The coordinator will keep trying on the regular update interval
    
    # Create sensors for battery status (dynamic data)
    for description in BATTERY_STATUS_SENSORS:
        sensor = MarstekBatteryStatusSensor(coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created battery status sensor: %s", description.name)
    
    # Create data coordinator for mode status updates
    mode_coordinator = MarstekModeDataUpdateCoordinator(hass, client, device_id)
    
    # Perform initial mode data fetch (but don't fail if it doesn't work immediately)
    try:
        await mode_coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.warning("Initial mode data fetch failed, will retry later: %s", exc)
        # Don't fail setup, just continue without initial data
        # The coordinator will keep trying on the regular update interval
    
    # Create sensors for mode status (dynamic data)
    for description in MODE_STATUS_SENSORS:
        sensor = MarstekModeStatusSensor(mode_coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created mode status sensor: %s", description.name)
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Marstek sensors (%d device info + %d battery status + %d mode status)", 
                 len(sensors), len(DEVICE_INFO_SENSORS), len(BATTERY_STATUS_SENSORS), len(MODE_STATUS_SENSORS))


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
                _LOGGER.warning("Failed to fetch battery status - device may be busy or unreachable")
                # Return previous data if available, or empty dict for first attempt
                return getattr(self, 'data', {})
            
            # Extract the result section which contains the actual battery data
            result = battery_data.get("result", {})
            
            _LOGGER.debug("Battery status data: %s", result)
            return result
            
        except Exception as exception:
            _LOGGER.warning("Error communicating with battery API: %s", exception)
            # Return previous data if available, or empty dict for first attempt  
            return getattr(self, 'data', {})


class MarstekModeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Marstek mode data."""

    def __init__(self, hass: HomeAssistant, client, device_id: int):
        """Initialize."""
        self.client = client
        self.device_id = device_id
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_mode",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            mode_data = await self.client.get_mode_status(self.device_id)
            if mode_data is None:
                _LOGGER.warning("Failed to fetch mode status - device may be busy or unreachable")
                # Return previous data if available, or empty dict for first attempt
                return getattr(self, 'data', {})
            
            # Extract the result section which contains the actual mode data
            result = mode_data.get("result", {})
            
            _LOGGER.debug("Mode status data: %s", result)
            return result
            
        except Exception as exception:
            _LOGGER.warning("Error communicating with mode API: %s", exception)
            # Return previous data if available, or empty dict for first attempt  
            return getattr(self, 'data', {})


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
        
        # Get the raw value from the API response
        sensor_key = self.entity_description.key
        raw_value = self.coordinator.data.get(sensor_key)
        
        if raw_value is None:
            return None
        
        # Apply conversions based on the field
        if sensor_key == "bat_temp":
            # bat_temp should be divided by 10 (164.0 / 10 = 16.4°C)
            return round(float(raw_value) / 10, 1)
        elif sensor_key == "bat_capacity":
            # bat_capacity should be multiplied by 10 (512.0 * 10 = 5120 Wh)
            return round(float(raw_value) * 10, 1)
        elif sensor_key == "rated_capacity":
            # rated_capacity is already in correct unit (Wh)
            return round(float(raw_value), 1)
        elif sensor_key == "soc":
            # State of charge is already in percentage
            return int(raw_value)
        elif sensor_key == "error_code":
            # Error code as string
            return str(raw_value)
        
        return raw_value
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)


class MarstekModeStatusSensor(SensorEntity):
    """Sensor for Marstek mode status information."""
    
    def __init__(self, coordinator: MarstekModeDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_mode_{description.key}"
        
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
        
        # Get the raw value from the API response
        sensor_key = self.entity_description.key
        
        # Handle the special case of bat_soc from mode (different from battery status)
        if sensor_key == "bat_soc_mode":
            raw_value = self.coordinator.data.get("bat_soc")
        else:
            raw_value = self.coordinator.data.get(sensor_key)
        
        if raw_value is None:
            return None
        
        # Apply conversions if needed
        if sensor_key in ["ongrid_power", "offgrid_power"]:
            # Power values are already in watts
            return int(raw_value)
        elif sensor_key == "bat_soc_mode":
            # State of charge is already in percentage
            return int(raw_value)
        elif sensor_key == "mode":
            # Mode as string
            return str(raw_value)
        
        return raw_value
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)