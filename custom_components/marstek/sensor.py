"""Sensor platform for Marstek integration."""
import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity

from .const import DOMAIN

# Two intervals: fast updates (ES.GetMode) and slow updates (EM, WiFi, BLE, Bat)
FAST_SCAN_INTERVAL = timedelta(seconds=10)       # 10 seconds for mode/battery
SLOW_SCAN_INTERVAL = timedelta(seconds=600)      # 10 minutes for other status

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

# Define sensor descriptions for energy meter status (from EM.GetStatus response)
EM_STATUS_SENSORS = [
    SensorEntityDescription(
        key="ct_state",
        name="CT State",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="a_power",
        name="Phase A Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SensorEntityDescription(
        key="b_power",
        name="Phase B Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SensorEntityDescription(
        key="c_power",
        name="Phase C Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),
    SensorEntityDescription(
        key="total_power",
        name="Total Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
]

# Define sensor descriptions for WiFi status (from Wifi.GetStatus response)
WIFI_STATUS_SENSORS = [
    SensorEntityDescription(
        key="ssid",
        name="WiFi SSID",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rssi",
        name="WiFi Signal Strength",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wifi-strength-2",
    ),
    SensorEntityDescription(
        key="sta_ip",
        name="Station IP Address",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="sta_gate",
        name="Gateway IP",
        icon="mdi:router-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="sta_mask",
        name="Subnet Mask",
        icon="mdi:ip-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="sta_dns",
        name="DNS Server",
        icon="mdi:dns",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


# Define sensor descriptions for BLE status (from BLE.GetStatus response)
BLE_STATUS_SENSORS = [
    SensorEntityDescription(
        key="state",
        name="BLE Connection State",
        icon="mdi:bluetooth",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="ble_mac",
        name="BLE MAC Address",
        icon="mdi:bluetooth",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]

# Shared logging helper for endpoint results
def log_status_result(logger, device_id, endpoint: str, resp, data_section):
    if resp is not None:
        try:
            logger.info(
                f"Marstek: {endpoint} succeeded for device %s - fields=%s",
                device_id,
                list(data_section.keys()),
            )
        except Exception:
            logger.info(f"Marstek: {endpoint} succeeded for device %s", device_id)
    else:
        logger.info(f"Marstek: {endpoint} returned no response for device %s", device_id)


def _create_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Create device info from config entry data."""
    ble_mac = config_entry.data.get("ble_mac")
    wifi_mac = config_entry.data.get("wifi_mac")
    device_ip = config_entry.data.get("device_ip")
    device_name = config_entry.data.get("device_name", "Marstek Device")
    wifi_name = config_entry.data.get("wifi_name")
    
    return DeviceInfo(
        identifiers={(DOMAIN, ble_mac or wifi_mac or device_ip)},
        manufacturer="Marstek",
        model=device_name,
        name=f"{device_name} ({wifi_name})" if wifi_name else device_name,
        sw_version=str(config_entry.data.get("device_version")) if config_entry.data.get("device_version") else None,
    )


class MarstekCoordinatorEntity(CoordinatorEntity, SensorEntity):
    """Base class for Marstek sensors using a coordinator."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: SensorEntityDescription,
        unique_id_prefix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{unique_id_prefix}_{description.key}"
        self._attr_device_info = _create_device_info(config_entry)
    
    def _get_value_from_section(self, section_key: str = None) -> any:
        """Helper to extract value from coordinator data with optional section key."""
        if self.coordinator.data is None:
            return None
        
        # If section_key provided, get data from that section
        if section_key:
            section = self.coordinator.data.get(section_key, {})
            return section.get(self.entity_description.key)
        
        # Otherwise get directly from root
        return self.coordinator.data.get(self.entity_description.key)


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
    
    # Create fast coordinator for ES.GetMode (updates every 10 seconds)
    fast_coordinator = MarstekDataUpdateCoordinator(hass, client, device_id)
    
    # Create slow coordinator for EM/WiFi/BLE/Bat status (updates every 60 minutes)
    slow_coordinator = MarstekStatusDataUpdateCoordinator(hass, client, device_id)
    
    # Create sensors for mode status (uses fast coordinator)
    for description in MODE_STATUS_SENSORS:
        sensors.append(MarstekModeStatusSensor(fast_coordinator, config_entry, description))
        _LOGGER.debug("Created mode status sensor: %s", description.name)
        
    # Create sensors for battery status (uses fast coordinator)
    for description in BATTERY_STATUS_SENSORS:
        sensors.append(MarstekBatteryStatusSensor(slow_coordinator, config_entry, description))
        _LOGGER.debug("Created battery status sensor: %s", description.name)

    # Create sensors for EM status (uses slow coordinator)
    for description in EM_STATUS_SENSORS:
        sensors.append(MarstekEMStatusSensor(slow_coordinator, config_entry, description))
        _LOGGER.debug("Created EM status sensor: %s", description.name)

    # Create sensors for WiFi status (uses slow coordinator)
    for description in WIFI_STATUS_SENSORS:
        sensors.append(MarstekWifiStatusSensor(slow_coordinator, config_entry, description))
        _LOGGER.debug("Created WiFi status sensor: %s", description.name)

    # Create sensors for BLE status (uses slow coordinator)
    for description in BLE_STATUS_SENSORS:
        sensors.append(MarstekBLEStatusSensor(slow_coordinator, config_entry, description))
        _LOGGER.debug("Created BLE status sensor: %s", description.name)
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Marstek sensors (%d device info + %d battery + %d mode + %d EM + %d WiFi + %d BLE)", 
                 len(sensors), len(DEVICE_INFO_SENSORS), len(BATTERY_STATUS_SENSORS), len(MODE_STATUS_SENSORS), len(EM_STATUS_SENSORS), len(WIFI_STATUS_SENSORS), len(BLE_STATUS_SENSORS))

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
            update_interval=FAST_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via ES.GetMode only."""
        try:
            mode_data = await self.client.get_mode_status(self.device_id)
            result = mode_data.get("result", {}) if mode_data is not None else {}

            _LOGGER.debug("Mode status data: %s", result)
            log_status_result(_LOGGER, self.device_id, "ES.GetMode", mode_data, result)

            if mode_data is None:
                # Return previous data if available, or empty dict for first attempt
                return getattr(self, 'data', {})
            return result

        except Exception as exception:
            _LOGGER.warning("Error communicating with mode API: %s", exception)
            # Return previous data if available, or empty dict for first attempt  
            return getattr(self, 'data', {})

class MarstekStatusDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches mode, EM, WiFi and BLE in one update."""

    def __init__(self, hass: HomeAssistant, client, device_id: int):
        self.client = client
        self.device_id = device_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_status",
            update_interval=SLOW_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch EM, WiFi, BLE, and Bat status sequentially and return combined dict."""
        data = {}
        try:
            em_resp = await self.client.get_em_status(self.device_id)
            wifi_resp = await self.client.get_wifi_status(self.device_id)
            ble_resp = await self.client.get_ble_status(self.device_id)
            bat_resp = await self.client.get_battery_status(self.device_id)
            
            data["em"] = (em_resp or {}).get("result", {}) if em_resp is not None else getattr(self, 'data', {}).get("em", {})
            data["wifi"] = (wifi_resp or {}).get("result", {}) if wifi_resp is not None else getattr(self, 'data', {}).get("wifi", {})
            data["ble"] = (ble_resp or {}).get("result", {}) if ble_resp is not None else getattr(self, 'data', {}).get("ble", {})
            data["bat"] = (bat_resp or {}).get("result", {}) if bat_resp is not None else getattr(self, 'data', {}).get("bat", {})

            # Log results for each endpoint using shared helper
            log_status_result(_LOGGER, self.device_id, "EM.GetStatus", em_resp, data["em"])
            log_status_result(_LOGGER, self.device_id, "Wifi.GetStatus", wifi_resp, data["wifi"])
            log_status_result(_LOGGER, self.device_id, "BLE.GetStatus", ble_resp, data["ble"])
            log_status_result(_LOGGER, self.device_id, "Bat.GetStatus", bat_resp, data["bat"])

            _LOGGER.debug("Combined status data: %s", data)
            return data

        except Exception as exc:
            _LOGGER.warning("Error fetching combined status data: %s", exc)
            return getattr(self, 'data', {})

class MarstekDeviceInfoSensor(SensorEntity):
    """Sensor for Marstek device information."""
    
    def __init__(self, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = _create_device_info(config_entry)
        self._attr_native_value = config_entry.data.get(description.key)
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._config_entry.data.get(self.entity_description.key)

class MarstekModeStatusSensor(MarstekCoordinatorEntity):
    """Sensor for Marstek mode status information."""
    
    def __init__(self, coordinator: MarstekDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, description, "mode")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        sensor_key = self.entity_description.key
        
        # Special case: bat_soc_mode reads from bat_soc field
        if sensor_key == "bat_soc_mode":
            if self.coordinator.data is None:
                _LOGGER.warning("Mode sensor bat_soc_mode: coordinator data is None")
                return None
            raw_value = self.coordinator.data.get("bat_soc")
            _LOGGER.debug("Mode sensor bat_soc_mode: raw_value=%s from coordinator data keys=%s", 
                         raw_value, list(self.coordinator.data.keys()))
        else:
            raw_value = self._get_value_from_section()
            _LOGGER.debug("Mode sensor %s: raw_value=%s from coordinator data keys=%s", 
                         sensor_key, raw_value, list(self.coordinator.data.keys()) if self.coordinator.data else None)

        if raw_value is None:
            _LOGGER.warning("Mode sensor %s: raw_value is None after lookup", sensor_key)
            return None

        # Apply conversions
        if sensor_key in ["ongrid_power", "offgrid_power"]:
            return int(raw_value)
        elif sensor_key == "bat_soc_mode":
            return int(raw_value)
        elif sensor_key == "mode":
            return str(raw_value)

        return raw_value
    
class MarstekBatteryStatusSensor(MarstekCoordinatorEntity):
    """Sensor for Marstek battery status information."""
    
    def __init__(self, coordinator: MarstekStatusDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, description, "battery")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        raw_value = self._get_value_from_section("bat")
        if raw_value is None:
            return None
        
        sensor_key = self.entity_description.key
        
        # Apply conversions based on the field
        if sensor_key == "bat_temp":
            return round(float(raw_value) / 10, 1)  # 164.0 / 10 = 16.4°C
        elif sensor_key == "bat_capacity":
            return round(float(raw_value) * 10, 1)  # 512.0 * 10 = 5120 Wh
        elif sensor_key == "rated_capacity":
            return round(float(raw_value), 1)
        elif sensor_key == "soc":
            return int(raw_value)
        elif sensor_key == "error_code":
            return str(raw_value)
        
        return raw_value

class MarstekEMStatusSensor(MarstekCoordinatorEntity):
    """Sensor for Marstek energy meter status information."""
    
    def __init__(self, coordinator: MarstekStatusDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, description, "em")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        raw_value = self._get_value_from_section("em")
        if raw_value is None:
            return None
        
        sensor_key = self.entity_description.key
        
        # Apply conversions
        if sensor_key in ["a_power", "b_power", "c_power", "total_power"]:
            return int(raw_value)
        elif sensor_key == "ct_state":
            return int(raw_value)
        
        return raw_value


class MarstekWifiStatusSensor(MarstekCoordinatorEntity):
    """Sensor for Marstek WiFi status information."""
    
    def __init__(self, coordinator: MarstekStatusDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, description, "wifi")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        raw_value = self._get_value_from_section("wifi")
        if raw_value is None:
            return None
        
        sensor_key = self.entity_description.key
        
        # Apply conversions
        if sensor_key == "rssi":
            return int(raw_value)
        elif sensor_key in ["ssid", "sta_ip", "sta_gate", "sta_mask", "sta_dns"]:
            return str(raw_value)
        
        return raw_value


class MarstekBLEStatusSensor(MarstekCoordinatorEntity):
    """Sensor for Marstek BLE status information."""
    
    def __init__(self, coordinator: MarstekStatusDataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, description, "ble")
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        raw_value = self._get_value_from_section("ble")
        if raw_value is None:
            return None
        
        sensor_key = self.entity_description.key
        
        # Apply conversions
        if sensor_key in ["state", "ble_mac"]:
            return str(raw_value)
        
        return raw_value
