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
        
    async def _send_rpc_request(self, method: str, params: dict):
        # Rate limiting: ensure minimum interval between requests
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            _LOGGER.debug("Rate limiting: waiting %.2f seconds before next request", sleep_time)
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        _LOGGER.info("Sending %s to %s:%s with params: %s", method, self.device_ip, self.remote_port, params)
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Try to bind to the local port, with fallback if occupied
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    port_to_try = self.local_port + attempt
                    sock.bind(('', port_to_try))
                    if attempt > 0:
                        _LOGGER.debug("Bound to port %d (original %d was busy)", port_to_try, self.local_port)
                    break
                except OSError as e:
                    if attempt == max_retries - 1:
                        raise e
                    _LOGGER.debug("Port %d busy, trying %d", port_to_try, port_to_try + 1)
            
            sock.settimeout(10)  # 10 second timeout
            
            rpc_id = random.randint(1000, 65000)
            req = {
                "id": rpc_id,
                "method": method,
                "params": params
            }
            
            message = json.dumps(req).encode('utf-8')
            _LOGGER.info("REQUEST: %s", message.decode('utf-8'))
            
            sock.sendto(message, (self.device_ip, self.remote_port))
            response, addr = sock.recvfrom(4096)
            
            txt = response.decode('utf-8')
            _LOGGER.info("RESPONSE: %s", txt)
            
            obj = json.loads(txt)            
            return obj
            
        except Exception as e:
            _LOGGER.error("Error sending %s request: %s", method, e)
            return None
        finally:
            if sock:
                sock.close()
        
    async def get_device_info(self, ble_mac: str):
        ble_mac_str = str(ble_mac)        
        params = {"ble_mac": ble_mac_str}
        return await self._send_rpc_request("Marstek.GetDevice", params)
    
    async def get_battery_status(self, device_id: int):
        params = {"id": device_id}
        return await self._send_rpc_request("Bat.GetStatus", params)