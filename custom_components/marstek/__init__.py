"""Simple Marstek integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek integration - discover devices and save device info."""
    _LOGGER.info("Setting up Marstek integration")

    device_ip = entry.data["device_ip"]
    remote_port = entry.data.get("remote_port", 30000)
    local_port = entry.data.get("local_port", 30000)

    # Create client with increased timeout for slower device responses
    client = MarstekUDPClient(device_ip, remote_port, local_port)
    
    # Use device information already gathered during config_flow
    rpc_id = entry.data.get("device_id")
    if rpc_id is None:
        _LOGGER.error("No device ID found in entry data - config flow may have failed")
        raise ConfigEntryNotReady("Device ID not found in config entry data")

    # Build device info from stored config entry data
    payload = {
        "device": entry.data.get("device_name"),
        "ver": entry.data.get("device_version"),
        "ble_mac": entry.data.get("ble_mac"),
        "wifi_mac": entry.data.get("wifi_mac"),
        "wifi_name": entry.data.get("wifi_name"),
        "ip": entry.data.get("device_reported_ip"),
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    src = f"{payload.get('device', 'Unknown')} {payload.get('ver', '')}-{payload.get('ble_mac', 'unknown')}"

    # Validate that we have essential device information
    if not payload.get("ble_mac") and not payload.get("wifi_mac"):
        _LOGGER.error("No MAC address found in device data")
        raise ConfigEntryNotReady("No MAC address found in device data")

    # The payload contains device info. Build devices mapping keyed by ble_mac.
    hass.data.setdefault(DOMAIN, {})
    devices = {}

    def _add_device_from_result(res):
        if not isinstance(res, dict):
            return
        ble = res.get("ble_mac") or res.get("mac")
        if not ble:
            return
        # Copy device fields and attach rpc metadata
        info = dict(res)
        info["rpc_id"] = rpc_id
        if src:
            info["src"] = src
        devices[str(ble)] = info

    # payload can be a dict for a single device, or a list of devices
    if isinstance(payload, dict):
        _add_device_from_result(payload)
    elif isinstance(payload, list):
        for item in payload:
            _add_device_from_result(item)
    else:
        _LOGGER.debug("Unexpected payload type in RPC result: %s", type(payload))

    if not devices:
        _LOGGER.warning("No devices discovered during setup")

    # Register device in Home Assistant's device registry
    device_registry = dr.async_get(hass)
    
    # Use the data from config entry if available, otherwise fall back to discovered data
    device_name = entry.data.get("device_name") or "Marstek Device"
    device_version = entry.data.get("device_version")
    wifi_mac = entry.data.get("wifi_mac")
    ble_mac = entry.data.get("ble_mac")
    wifi_name = entry.data.get("wifi_name")
    
    # Create a more descriptive device name
    if wifi_name:
        device_title = f"{device_name} ({wifi_name})"
    else:
        device_title = device_name
    
    # Register the device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, ble_mac or wifi_mac or device_ip)},
        manufacturer="Marstek",
        model=device_name,
        name=device_title,
        sw_version=str(device_version) if device_version else None,
        connections=set(),
    )

    # Store integration data before forwarding to platforms
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "rpc_id": rpc_id, "devices": devices}

    # Validate that we have all required data before forwarding to sensor platform
    try:
        # Forward setup to sensor platform
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    except Exception as exc:
        _LOGGER.exception("Failed to set up sensor platform: %s", exc)
        # Clean up on failure
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise ConfigEntryNotReady(f"Failed to set up sensor platform: {exc}")

    _LOGGER.info("Setup complete - discovered %d devices (rpc id: %s)", len(devices), rpc_id)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    # Unload sensor platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok