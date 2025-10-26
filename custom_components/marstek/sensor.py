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

# Two intervals: battery (faster) and combined status (slower)
BATTERY_SCAN_INTERVAL = timedelta(minutes=1)
STATUS_SCAN_INTERVAL = timedelta(minutes=5)

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
    # NOTE: intentionally not awaiting an initial refresh here to avoid
    # a burst of RPCs during integration setup. The coordinator will
    # perform its first update on its scheduled `BATTERY_SCAN_INTERVAL`.
    
    # Create sensors for battery status (dynamic data)
    for description in BATTERY_STATUS_SENSORS:
        sensor = MarstekBatteryStatusSensor(coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created battery status sensor: %s", description.name)
    
    # Create a single combined data coordinator for mode, EM, WiFi and BLE status updates
    status_coordinator = MarstekStatusDataUpdateCoordinator(hass, client, device_id)
    # NOTE: intentionally not awaiting an initial refresh here to avoid
    # sending multiple RPCs immediately when the integration is added.
    # The coordinator will perform its first update on its scheduled
    # `STATUS_SCAN_INTERVAL`.

    # Create sensors for mode, EM, WiFi and BLE (dynamic data) using the combined coordinator
    for description in MODE_STATUS_SENSORS:
        sensor = MarstekModeStatusSensor(status_coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created mode status sensor: %s", description.name)

    for description in EM_STATUS_SENSORS:
        sensor = MarstekEMStatusSensor(status_coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created EM status sensor: %s", description.name)

    for description in WIFI_STATUS_SENSORS:
        sensor = MarstekWifiStatusSensor(status_coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created WiFi status sensor: %s", description.name)

    for description in BLE_STATUS_SENSORS:
        sensor = MarstekBLEStatusSensor(status_coordinator, config_entry, description)
        sensors.append(sensor)
        _LOGGER.debug("Created BLE status sensor: %s", description.name)
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Marstek sensors (%d device info + %d battery + %d mode + %d EM + %d WiFi + %d BLE)", 
                 len(sensors), len(DEVICE_INFO_SENSORS), len(BATTERY_STATUS_SENSORS), len(MODE_STATUS_SENSORS), len(EM_STATUS_SENSORS), len(WIFI_STATUS_SENSORS), len(BLE_STATUS_SENSORS))


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
            update_interval=BATTERY_SCAN_INTERVAL,
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
            # Log successful battery query
            try:
                _LOGGER.info(
                    "Marstek: Bat.GetStatus succeeded for device %s - fields=%s",
                    self.device_id,
                    list(result.keys()),
                )
            except Exception:
                _LOGGER.info("Marstek: Bat.GetStatus succeeded for device %s", self.device_id)
            return result
            
        except Exception as exception:
            _LOGGER.warning("Error communicating with battery API: %s", exception)
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
            update_interval=STATUS_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch multiple endpoints sequentially and return combined dict."""
        data = {}
        try:
            # Fetch sequentially to respect client rate limits
            mode_resp = await self.client.get_mode_status(self.device_id)
            em_resp = await self.client.get_em_status(self.device_id)
            wifi_resp = await self.client.get_wifi_status(self.device_id)
            ble_resp = await self.client.get_ble_status(self.device_id)

            data["mode"] = (mode_resp or {}).get("result", {}) if mode_resp is not None else getattr(self, 'data', {}).get("mode", {})
            data["em"] = (em_resp or {}).get("result", {}) if em_resp is not None else getattr(self, 'data', {}).get("em", {})
            data["wifi"] = (wifi_resp or {}).get("result", {}) if wifi_resp is not None else getattr(self, 'data', {}).get("wifi", {})
            data["ble"] = (ble_resp or {}).get("result", {}) if ble_resp is not None else getattr(self, 'data', {}).get("ble", {})

            # Log successes for each endpoint
            if mode_resp is not None:
                try:
                    _LOGGER.info(
                        "Marstek: ES.GetMode succeeded for device %s - fields=%s",
                        self.device_id,
                        list(data["mode"].keys()),
                    )
                except Exception:
                    _LOGGER.info("Marstek: ES.GetMode succeeded for device %s", self.device_id)
            else:
                _LOGGER.info("Marstek: ES.GetMode returned no response for device %s", self.device_id)

            if em_resp is not None:
                try:
                    _LOGGER.info(
                        "Marstek: EM.GetStatus succeeded for device %s - fields=%s",
                        self.device_id,
                        list(data["em"].keys()),
                    )
                except Exception:
                    _LOGGER.info("Marstek: EM.GetStatus succeeded for device %s", self.device_id)
            else:
                _LOGGER.info("Marstek: EM.GetStatus returned no response for device %s", self.device_id)

            if wifi_resp is not None:
                try:
                    _LOGGER.info(
                        "Marstek: Wifi.GetStatus succeeded for device %s - fields=%s",
                        self.device_id,
                        list(data["wifi"].keys()),
                    )
                except Exception:
                    _LOGGER.info("Marstek: Wifi.GetStatus succeeded for device %s", self.device_id)
            else:
                _LOGGER.info("Marstek: Wifi.GetStatus returned no response for device %s", self.device_id)

            if ble_resp is not None:
                try:
                    _LOGGER.info(
                        "Marstek: BLE.GetStatus succeeded for device %s - fields=%s",
                        self.device_id,
                        list(data["ble"].keys()),
                    )
                except Exception:
                    _LOGGER.info("Marstek: BLE.GetStatus succeeded for device %s", self.device_id)
            else:
                _LOGGER.info("Marstek: BLE.GetStatus returned no response for device %s", self.device_id)

            _LOGGER.debug("Combined status data: %s", data)
            return data

        except Exception as exc:
            _LOGGER.warning("Error fetching combined status data: %s", exc)
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
    
    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
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

        # The combined coordinator stores mode data under the 'mode' key
        section = self.coordinator.data.get("mode", {})
        sensor_key = self.entity_description.key

        # Handle the special case of bat_soc from mode (different from battery status)
        if sensor_key == "bat_soc_mode":
            raw_value = section.get("bat_soc")
        else:
            raw_value = section.get(sensor_key)
        
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


class MarstekEMStatusSensor(SensorEntity):
    """Sensor for Marstek energy meter status information."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_em_{description.key}"
        
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

        # The combined coordinator stores EM data under the 'em' key
        section = self.coordinator.data.get("em", {})
        sensor_key = self.entity_description.key
        raw_value = section.get(sensor_key)
        
        if raw_value is None:
            return None
        
        # Apply conversions if needed
        if sensor_key in ["a_power", "b_power", "c_power", "total_power"]:
            # Power values are already in watts
            return int(raw_value)
        elif sensor_key == "ct_state":
            # CT state as integer
            return int(raw_value)
        
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


class MarstekWifiStatusSensor(SensorEntity):
    """Sensor for Marstek WiFi status information."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_wifi_{description.key}"
        
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

        # The combined coordinator stores WiFi data under the 'wifi' key
        section = self.coordinator.data.get("wifi", {})
        sensor_key = self.entity_description.key
        raw_value = section.get(sensor_key)
        
        if raw_value is None:
            return None
        
        # Apply conversions if needed
        if sensor_key == "rssi":
            # RSSI value as integer (dBm)
            return int(raw_value)
        elif sensor_key in ["ssid", "sta_ip", "sta_gate", "sta_mask", "sta_dns"]:
            # Network info as strings
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


class MarstekBLEStatusSensor(SensorEntity):
    """Sensor for Marstek BLE status information."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, config_entry: ConfigEntry, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_ble_{description.key}"
        
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

        # The combined coordinator stores BLE data under the 'ble' key
        section = self.coordinator.data.get("ble", {})
        sensor_key = self.entity_description.key
        raw_value = section.get(sensor_key)
        
        if raw_value is None:
            return None
        
        # Apply conversions if needed
        if sensor_key in ["state", "ble_mac"]:
            # BLE info as strings
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