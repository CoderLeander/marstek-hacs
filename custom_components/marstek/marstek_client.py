"""Simple Marstek UDP Client."""
import socket
import json
import random
import logging
import asyncio
import time

_LOGGER = logging.getLogger(__name__)

class MarstekUDPClient:
    """Simple UDP client for Marstek.GetDevice command only."""
    
    def __init__(self, device_ip: str, remote_port: int = 30000, local_port: int = 30000):
        self.device_ip = device_ip
        self.remote_port = remote_port
        self.local_port = local_port
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests
        
    async def get_device_info(self, ble_mac: str):
        """Send Marstek.GetDevice command once with rate limiting.

        Returns the full parsed RPC response (dict) so callers can access the
        top-level "id" which is required for subsequent API calls.
        
        Args:
            ble_mac: BLE MAC address as string. Use "0" for discovery of all devices.
        """
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            _LOGGER.debug("Rate limiting: waiting %.2f seconds before next request", sleep_time)
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        _LOGGER.info("Sending Marstek.GetDevice to %s:%s with BLE MAC: %s", self.device_ip, self.remote_port, ble_mac)
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(10)  # Extended timeout from 5 to 10 seconds
            
            rpc_id = random.randint(1000, 65000)
            # Ensure ble_mac is always a string
            ble_mac_str = str(ble_mac)
            req = {
                "id": rpc_id,
                "method": "Marstek.GetDevice",
                "params": {"ble_mac": ble_mac_str}
            }
            
            message = json.dumps(req).encode('utf-8')
            _LOGGER.info("REQUEST: %s", message.decode('utf-8'))
            
            sock.sendto(message, (self.device_ip, self.remote_port))
            response, addr = sock.recvfrom(4096)
            
            txt = response.decode('utf-8')
            # Log the full response (including id) because the id is required
            # for subsequent API calls.
            _LOGGER.info("RESPONSE: %s", txt)
            
            obj = json.loads(txt)
            
            # Log the response ID specifically for tracking
            if "id" in obj:
                _LOGGER.info("Response ID: %s", obj["id"])
            else:
                _LOGGER.warning("No 'id' field found in response")
            
            return obj
            
        except Exception as e:
            _LOGGER.error("Error: %s", e)
            return None
        finally:
            if sock:
                sock.close()
    
    async def test_connection(self, ble_mac: str) -> bool:
        result = await self.get_device_info(ble_mac)
        return result is not None
    
    async def get_battery_status(self, device_id: int):
        """Send ES.GetStatus command to retrieve battery information.
        
        Args:
            device_id: The device ID returned from the GetDevice call.
            
        Returns:
            Full parsed RPC response (dict) containing battery status information.
        """
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            _LOGGER.debug("Rate limiting: waiting %.2f seconds before next request", sleep_time)
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        _LOGGER.info("Sending ES.GetStatus to %s:%s with device ID: %s", self.device_ip, self.remote_port, device_id)
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(10)  # 10 second timeout
            
            rpc_id = random.randint(1000, 65000)
            req = {
                "id": rpc_id,
                "method": "ES.GetStatus",
                "params": {"id": device_id}
            }
            
            message = json.dumps(req).encode('utf-8')
            _LOGGER.info("REQUEST: %s", message.decode('utf-8'))
            
            sock.sendto(message, (self.device_ip, self.remote_port))
            response, addr = sock.recvfrom(4096)
            
            txt = response.decode('utf-8')
            _LOGGER.info("RESPONSE: %s", txt)
            
            obj = json.loads(txt)
            
            # Log the response ID specifically for tracking
            if "id" in obj:
                _LOGGER.info("Response ID: %s", obj["id"])
            else:
                _LOGGER.warning("No 'id' field found in response")
            
            return obj
            
        except Exception as e:
            _LOGGER.error("Error getting battery status: %s", e)
            return None
        finally:
            if sock:
                sock.close()