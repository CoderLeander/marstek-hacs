"""Simple Marstek UDP Client."""
import socket
import json
import random
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

class MarstekUDPClient:
    """Simple UDP client for Marstek.GetDevice command only."""
    
    def __init__(self, device_ip: str, remote_port: int = 30000, local_port: int = 30000):
        self.device_ip = device_ip
        self.remote_port = remote_port
        self.local_port = local_port
        
    async def get_device_info(self, ble_mac: str):
        """Send Marstek.GetDevice command once."""
        _LOGGER.info("Sending Marstek.GetDevice to %s:%s with BLE MAC: %s", 
                     self.device_ip, self.remote_port, ble_mac)
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(5)
            
            rpc_id = random.randint(1000, 65000)
            req = {
                "id": rpc_id,
                "method": "Marstek.GetDevice",
                "params": {"ble_mac": ble_mac}
            }
            
            message = json.dumps(req).encode('utf-8')
            _LOGGER.info("REQUEST: %s", message.decode('utf-8'))
            
            sock.sendto(message, (self.device_ip, self.remote_port))
            response, addr = sock.recvfrom(4096)
            
            txt = response.decode('utf-8')
            _LOGGER.info("RESPONSE: %s", txt)
            
            obj = json.loads(txt)
            return obj.get("result", {}) if "result" in obj else None
            
        except Exception as e:
            _LOGGER.error("Error: %s", e)
            return None
        finally:
            if sock:
                sock.close()
    
    async def test_connection(self, ble_mac: str) -> bool:
        """Test connection by sending Marstek.GetDevice once."""
        result = await self.get_device_info(ble_mac)
        return result is not None
    
