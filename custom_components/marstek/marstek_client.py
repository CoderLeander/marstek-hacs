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
            _LOGGER.debug(f"Sending [{rpc_id}] {method} to {self.device_ip}:{self.remote_port}")
            _LOGGER.debug(f"Request payload: {message.decode('utf-8')}")
            sock.sendto(message, (self.device_ip, self.remote_port))
            
            # Wait for response
            response, addr = sock.recvfrom(4096)
            
            # Convert the received bytes back to a string
            txt = response.decode('utf-8')
            
            # Parse the JSON response back into a Python object
            obj = json.loads(txt)
            
            _LOGGER.info(f"Response [{rpc_id}] from {addr}: {txt}")
            
            # Check if there's an error in the response
            if "error" in obj:
                _LOGGER.error(f"Device returned error: {obj['error']}")
                return None
                
            return obj
            
        except socket.timeout:
            _LOGGER.warning(f"Timeout after {self.timeout} seconds for method {method}")
            return None
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"Error communicating with device: {e}")
            return None
        finally:
            if sock:
                sock.close()
    
    async def get_device_info(self, ble_mac: str) -> Optional[Dict[str, Any]]:
        """Get device information.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            Device information or None if failed
        """
        _LOGGER.info("Getting device info for BLE MAC: %s", ble_mac)
        
        # Try different possible methods
        methods_to_try = [
            ("Marstek.GetDevice", {"ble_mac": ble_mac}),
            ("GetDevice", {"ble_mac": ble_mac}),
            ("get_device_info", {"ble_mac": ble_mac}),
            ("device_info", {"mac": ble_mac}),
            ("status", {}),
            ("get_status", {}),
        ]
        
        for method, params in methods_to_try:
            _LOGGER.info("Trying method: %s with params: %s", method, params)
            result = await self.send_command(method, params)
            if result is not None:
                _LOGGER.info("Success with method %s: %s", method, result)
                return result
            else:
                _LOGGER.warning("Method %s failed", method)
        
        _LOGGER.error("All methods failed for device info")
        return None
    
    async def test_connection(self, ble_mac: str) -> bool:
        """Test if the device is reachable.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            True if device responds, False otherwise
        """
        _LOGGER.info("Testing connection to device with BLE MAC: %s", ble_mac)
        
        # First try a simple ping-like command
        simple_commands = [
            ("ping", {}),
            ("status", {}),
            ("hello", {}),
        ]
        
        for method, params in simple_commands:
            result = await self.send_command(method, params)
            if result is not None:
                _LOGGER.info("Device responded to %s command", method)
                return True
        
        # If simple commands fail, try the device info
        result = await self.get_device_info(ble_mac)
        success = result is not None
        _LOGGER.info("Connection test result: %s", success)
        return success