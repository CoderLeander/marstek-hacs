"""Simple Marstek integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .marstek_client import MarstekUDPClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marstek integration - discover devices and save device info."""
    _LOGGER.info("Setting up Marstek integration")

    device_ip = entry.data["device_ip"]
    remote_port = entry.data.get("remote_port", 30000)
    local_port = entry.data.get("local_port", 30000)

    # Create client and request discovery (ble_mac=0)
    client = MarstekUDPClient(device_ip, remote_port, local_port)
    rpc_response = await client.get_device_info(0)

    if rpc_response is None:
        _LOGGER.error("Failed to get device info during setup")
        return False

    # Expect the client to return the full RPC object: {"id":..., "src":..., "result": ...}
    if not isinstance(rpc_response, dict):
        _LOGGER.error("Unexpected RPC response type: %s", type(rpc_response))
        return False

    rpc_id = rpc_response.get("id")
    src = rpc_response.get("src")
    payload = rpc_response.get("result")

    if payload is None:
        _LOGGER.error("RPC response missing 'result' payload")
        return False

    # The payload usually contains device info. Build devices mapping keyed by ble_mac.
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

    hass.data[DOMAIN][entry.entry_id] = {"client": client, "rpc_id": rpc_id, "devices": devices}

    _LOGGER.info("Setup complete - discovered %d devices (rpc id: %s)", len(devices), rpc_id)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True