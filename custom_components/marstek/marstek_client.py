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
            sock.sendto(message, (self.device_ip, self.remote_port))
            
            # Wait for response
            response, addr = sock.recvfrom(4096)
            
            # Convert the received bytes back to a string
            txt = response.decode('utf-8')
            
            # Parse the JSON response back into a Python object
            obj = json.loads(txt)
            
            _LOGGER.debug(f"Response [{rpc_id}] from {addr}: {txt}")
            return obj
            
        except socket.timeout:
            _LOGGER.warning(f"Timeout after {self.timeout} seconds for method {method}")
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
        return await self.send_command("Marstek.GetDevice", {"ble_mac": ble_mac})
    
    async def test_connection(self, ble_mac: str) -> bool:
        """Test if the device is reachable.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            True if device responds, False otherwise
        """
        result = await self.get_device_info(ble_mac)
        return result is not None