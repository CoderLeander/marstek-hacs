"""Constants for the Marstek Battery integration."""

DOMAIN = "marstek"

# Configuration keys
CONF_DEVICE_IP = "device_ip"
CONF_BLE_MAC = "ble_mac"
CONF_REMOTE_PORT = "remote_port"
CONF_LOCAL_PORT = "local_port"

# Default values
DEFAULT_REMOTE_PORT = 30000
DEFAULT_LOCAL_PORT = 30000
DEFAULT_TIMEOUT = 5

# Sensor types and their properties
SENSOR_TYPES = {
    "battery_voltage": {
        "name": "Battery Voltage",
        "unit": "V",
        "icon": "mdi:battery",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    "battery_current": {
        "name": "Battery Current", 
        "unit": "A",
        "icon": "mdi:current-dc",
        "device_class": "current",
        "state_class": "measurement",
    },
    "battery_power": {
        "name": "Battery Power",
        "unit": "W", 
        "icon": "mdi:flash",
        "device_class": "power",
        "state_class": "measurement",
    },
    "battery_temperature": {
        "name": "Battery Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature", 
        "state_class": "measurement",
    },
    "battery_soc": {
        "name": "Battery State of Charge",
        "unit": "%",
        "icon": "mdi:battery-50",
        "device_class": "battery",
        "state_class": "measurement",
    },
}