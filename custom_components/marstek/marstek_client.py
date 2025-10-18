"""Marstek UDP Communication Module."""
import socket
import json
import random
import logging
from typing import Optional, Dict, Any
import asyncio

_LOGGER = logging.getLogger(__name__)

class MarstekUDPClient:
    """UDP client for communicating with Marstek devices."""
    
    def __init__(self, device_ip: str, remote_port: int = 30000, local_port: int = 30000, timeout: int = 5):
        """Initialize the UDP client.
        
        Args:
            device_ip: IP address of the Marstek device
            remote_port: Port the device is listening on
            local_port: Port to bind to locally
            timeout: Maximum seconds to wait for a response
        """
        self.device_ip = device_ip
        self.remote_port = remote_port
        self.local_port = local_port
        self.timeout = timeout
        
    async def send_command(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a command to the Marstek device asynchronously.
        
        Args:
            method: The command/method to call on the device
            params: Parameters for the command
            
        Returns:
            Response from the device or None if failed
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._send_command_sync, method, params
        )
    
    def _send_command_sync(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a command to the Marstek device synchronously.
        
        Args:
            method: The command/method to call on the device
            params: Parameters for the command
            
        Returns:
            Response from the device or None if failed
        """
        sock = None
        try:
            # Create a UDP socket (connectionless, fast communication)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Allow reusing the address if the port was recently used
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to a specific local port
            sock.bind(('', self.local_port))
            
            # Set timeout
            sock.settimeout(self.timeout)
            
            # Create a unique ID for this request
            rpc_id = random.randint(1000, 65000)
            
            # Build the JSON-RPC request structure
            req = {
                "id": rpc_id,
                "method": method,
                "params": params
            }
            
            # Convert the request to JSON and then to bytes for transmission
            message = json.dumps(req, separators=(',', ':')).encode('utf-8')
            
            # Send the UDP packet to the device
            _LOGGER.info(f"📤 SENDING [{rpc_id}] {method} to {self.device_ip}:{self.remote_port}")
            _LOGGER.info(f"📤 REQUEST PAYLOAD: {message.decode('utf-8')}")
            sock.sendto(message, (self.device_ip, self.remote_port))
            
            # Wait for response
            response, addr = sock.recvfrom(4096)
            
            # Convert the received bytes back to a string
            txt = response.decode('utf-8')
            
            # Parse the JSON response back into a Python object
            obj = json.loads(txt)
            
            _LOGGER.info(f"📥 RESPONSE [{rpc_id}] from {addr}: {txt}")
            
            # Check if there's an error in the response
            if "error" in obj:
                _LOGGER.error(f"❌ DEVICE ERROR [{rpc_id}]: {obj['error']}")
                return None
            
            _LOGGER.info(f"✅ SUCCESS [{rpc_id}]: Command {method} completed successfully")
            return obj
            
        except socket.timeout:
            _LOGGER.warning(f"⏰ TIMEOUT [{method}]: No response after {self.timeout} seconds")
            return None
        except json.JSONDecodeError as e:
            _LOGGER.error(f"🔧 JSON DECODE ERROR [{method}]: Failed to parse response: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"💥 COMMUNICATION ERROR [{method}]: {e}")
            return None
        finally:
            if sock:
                sock.close()
    
    async def get_device_info(self, ble_mac: str) -> Optional[Dict[str, Any]]:
        """Get device information and all sensor data.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            Combined device and sensor information or None if failed
        """
        _LOGGER.info("Getting device info for BLE MAC: %s", ble_mac)
        
        # Get basic device info first
        device_result = await self.send_command("Marstek.GetDevice", {"ble_mac": ble_mac})
        if device_result is None or "error" in device_result:
            _LOGGER.error("Failed to get device info: %s", device_result)
            return None
        
        device_info = device_result.get("result", {})
        device_id = device_info.get("ble_mac", ble_mac)  # Use BLE MAC as device ID
        
        _LOGGER.info("Device info retrieved: %s", device_info)
        
        # Get all sensor data
        combined_data = {"device": device_info}
        
        # Get battery status
        bat_result = await self.send_command("Bat.GetStatus", {"id": device_id})
        if bat_result and "result" in bat_result:
            combined_data["battery"] = bat_result["result"]
            _LOGGER.info("Battery data: %s", bat_result["result"])
        
        # Get PV (solar) status
        pv_result = await self.send_command("PV.GetStatus", {"id": device_id})
        if pv_result and "result" in pv_result:
            combined_data["pv"] = pv_result["result"]
            _LOGGER.info("PV data: %s", pv_result["result"])
        
        # Get Energy Storage status
        es_result = await self.send_command("ES.GetStatus", {"id": device_id})
        if es_result and "result" in es_result:
            combined_data["energy_storage"] = es_result["result"]
            _LOGGER.info("ES data: %s", es_result["result"])
        
        # Get Energy Management status
        em_result = await self.send_command("EM.GetStatus", {"id": device_id})
        if em_result and "result" in em_result:
            combined_data["energy_management"] = em_result["result"]
            _LOGGER.info("EM data: %s", em_result["result"])
        
        # Get WiFi status
        wifi_result = await self.send_command("Wifi.GetStatus", {"id": device_id})
        if wifi_result and "result" in wifi_result:
            combined_data["wifi"] = wifi_result["result"]
            _LOGGER.info("WiFi data: %s", wifi_result["result"])
        
        # Get BLE status
        ble_result = await self.send_command("BLE.GetStatus", {"id": device_id})
        if ble_result and "result" in ble_result:
            combined_data["ble"] = ble_result["result"]
            _LOGGER.info("BLE data: %s", ble_result["result"])
        
        _LOGGER.info("Combined data collected: %s", combined_data)
        return combined_data
    
    async def get_battery_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get battery status."""
        result = await self.send_command("Bat.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_pv_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get PV (solar) status."""
        result = await self.send_command("PV.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_energy_storage_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get Energy Storage status."""
        result = await self.send_command("ES.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_energy_management_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get Energy Management status."""
        result = await self.send_command("EM.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_wifi_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get WiFi status."""
        result = await self.send_command("Wifi.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_ble_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get BLE status."""
        result = await self.send_command("BLE.GetStatus", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def get_energy_storage_mode(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get Energy Storage mode."""
        result = await self.send_command("ES.GetMode", {"id": device_id})
        return result.get("result") if result and "result" in result else None
    
    async def test_connection(self, ble_mac: str) -> bool:
        """Test if the device is reachable.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            True if device responds, False otherwise
        """
        _LOGGER.info("🔍 CONNECTION TEST: Starting test for device with BLE MAC: %s", ble_mac)
        
        # First try a very simple UDP ping to see if the device is listening
        _LOGGER.info("🔍 CONNECTION TEST: Step 1 - Raw UDP connectivity test")
        result = await self.send_raw_udp_test()
        if result:
            _LOGGER.info("✅ CONNECTION TEST: Raw UDP test successful - device is listening!")
        else:
            _LOGGER.warning("⚠️ CONNECTION TEST: Raw UDP test failed - device may not be listening")
        
        # First try a simple ping-like command
        _LOGGER.info("🔍 CONNECTION TEST: Step 2 - Trying simple command tests")
        simple_commands = [
            ("ping", {}),
            ("status", {}),
            ("hello", {}),
            ("info", {}),
        ]
        
        for method, params in simple_commands:
            _LOGGER.info("🔍 CONNECTION TEST: Trying command: %s", method)
            result = await self.send_command(method, params)
            if result is not None:
                _LOGGER.info("✅ CONNECTION TEST: Device responded to %s command!", method)
                return True
            _LOGGER.info("❌ CONNECTION TEST: No response to %s command", method)
        
        # If simple commands fail, try the device info
        _LOGGER.info("🔍 CONNECTION TEST: Step 3 - Trying device info retrieval")
        result = await self.get_device_info(ble_mac)
        success = result is not None
        
        if success:
            _LOGGER.info("✅ CONNECTION TEST: Successfully retrieved device info!")
        else:
            _LOGGER.error("❌ CONNECTION TEST: Failed to retrieve device info")
            _LOGGER.error("❌ CONNECTION TEST: Check the following:")
            _LOGGER.error("   - Device IP address (%s) is correct", self.device_ip)
            _LOGGER.error("   - Device is powered on and connected to network")
            _LOGGER.error("   - BLE MAC address (%s) is correct", ble_mac)
            _LOGGER.error("   - Remote port (%s) matches device configuration", self.remote_port)
            _LOGGER.error("   - Local port (%s) is not blocked by firewall", self.local_port)
        
        _LOGGER.info("🔍 CONNECTION TEST: Final result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def send_raw_udp_test(self) -> bool:
        """Send a raw UDP packet to test basic connectivity."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._send_raw_udp_test_sync
        )
    
    def _send_raw_udp_test_sync(self) -> bool:
        """Send a raw UDP packet synchronously."""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(2)  # Shorter timeout for ping
            
            # Send a simple test message
            test_message = b"PING"
            _LOGGER.info(f"📤 RAW UDP TEST: Sending to {self.device_ip}:{self.remote_port}")
            sock.sendto(test_message, (self.device_ip, self.remote_port))
            
            # Try to receive any response
            try:
                response, addr = sock.recvfrom(1024)
                _LOGGER.info(f"📥 RAW UDP TEST: Response from {addr}: {response}")
                return True
            except socket.timeout:
                _LOGGER.info("⏰ RAW UDP TEST: No response received (timeout)")
                return False
                
        except Exception as e:
            _LOGGER.error(f"💥 RAW UDP TEST ERROR: {e}")
            return False
        finally:
            if sock:
                sock.close()