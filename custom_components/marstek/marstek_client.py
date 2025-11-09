"""Simple Marstek UDP Client."""
import socket
import json
import random
import logging
import asyncio
import time
from typing import Optional

_LOGGER = logging.getLogger(__name__)

class MarstekUDPClient:
    """UDP client for Marstek device communication via RPC commands."""
    
    # Timing constants
    DEFAULT_SOCKET_TIMEOUT = 0.01  # 10ms quick check for incoming data
    DEFAULT_TOTAL_WAIT_TIME = 0.5  # 500ms total wait per attempt
    DEFAULT_MAX_SEND_ATTEMPTS = 3  # Maximum number of send attempts
    DEFAULT_RETRY_DELAY = 0.05  # 50ms delay between retry attempts
    DEFAULT_MIN_REQUEST_INTERVAL = 2.0  # Minimum 2 seconds between requests
    
    # Socket constants
    MAX_PORT_BIND_RETRIES = 5
    RECV_BUFFER_SIZE = 4096
    
    # Read-only methods that don't require strict ID matching
    READ_ONLY_METHODS = {
        "Marstek.GetDevice",
        "Bat.GetStatus",
        "EM.GetStatus",
        "Wifi.GetStatus",
        "BLE.GetStatus",
        "ES.GetMode",
    }
    
    def __init__(self, device_ip: str, remote_port: int = 30000, local_port: int = 30000,
                 socket_timeout: float = None, total_wait_time: float = None,
                 max_send_attempts: int = None, retry_delay: float = None):
        self.device_ip = device_ip
        self.remote_port = remote_port
        self.local_port = local_port
        self._last_request_time = 0
        self._min_request_interval = self.DEFAULT_MIN_REQUEST_INTERVAL
        
        # Allow customization of timing parameters
        self.socket_timeout = socket_timeout or self.DEFAULT_SOCKET_TIMEOUT
        self.total_wait_time = total_wait_time or self.DEFAULT_TOTAL_WAIT_TIME
        self.max_send_attempts = max_send_attempts or self.DEFAULT_MAX_SEND_ATTEMPTS
        self.retry_delay = retry_delay or self.DEFAULT_RETRY_DELAY
    
    def _bind_socket_with_retry(self, sock: socket.socket) -> None:
        """Bind socket to local port with retry fallback if port is occupied."""
        for attempt in range(self.MAX_PORT_BIND_RETRIES):
            try:
                port_to_try = self.local_port + attempt
                sock.bind(('', port_to_try))
                if attempt > 0:
                    _LOGGER.debug("Bound to port %d (original %d was busy)", port_to_try, self.local_port)
                return
            except OSError as e:
                if attempt == self.MAX_PORT_BIND_RETRIES - 1:
                    raise e
                _LOGGER.debug("Port %d busy, trying %d", port_to_try, port_to_try + 1)
    
    async def _wait_for_response(self, sock: socket.socket, rpc_id: int, method: str, start_time: float) -> tuple:
        """
        Wait for and validate UDP response.
        
        Args:
            sock: Socket to receive from
            rpc_id: Expected RPC ID
            method: RPC method name (for determining if strict ID matching is needed)
            start_time: Time when request was sent
        
        Returns:
            tuple: (success: bool, response_obj: dict or None, response_data: bytes)
        """
        response_data = b''
        is_read_only = method in self.READ_ONLY_METHODS
        
        while (time.time() - start_time) < self.total_wait_time:
            try:
                chunk, addr = sock.recvfrom(self.RECV_BUFFER_SIZE)
                
                # Validate response is from expected device
                if addr[0] != self.device_ip:
                    _LOGGER.warning("Received response from unexpected IP %s (expected %s)", addr[0], self.device_ip)
                    continue
                
                response_data += chunk
                
                # Try to parse as complete JSON
                try:
                    txt = response_data.decode('utf-8')
                    obj = json.loads(txt)
                    
                    # For read-only methods, accept any valid response
                    if is_read_only:
                        if obj.get("id") != rpc_id:
                            _LOGGER.debug("Response ID mismatch for read-only %s: expected %d, got %s (accepting anyway)", 
                                        method, rpc_id, obj.get("id"))
                        elapsed_ms = (time.time() - start_time) * 1000
                        _LOGGER.info("RESPONSE (received in %.0fms): %s", elapsed_ms, txt)
                        return (True, obj, response_data)
                    else:
                        # For write operations, enforce strict ID matching
                        if obj.get("id") != rpc_id:
                            _LOGGER.warning("Response ID mismatch for write operation %s: expected %d, got %s (rejecting)", 
                                          method, rpc_id, obj.get("id"))
                            continue
                        elapsed_ms = (time.time() - start_time) * 1000
                        _LOGGER.info("RESPONSE (received in %.0fms): %s", elapsed_ms, txt)
                        return (True, obj, response_data)
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Incomplete data, continue receiving
                    continue
                    
            except socket.timeout:
                # No data in this window, but continue waiting
                await asyncio.sleep(0.01)
                continue
        
        # Timeout - return what we got
        return (False, None, response_data)
        
    async def _send_rpc_request(self, method: str, params: dict) -> Optional[dict]:
        """
        Send RPC request to device with automatic retry logic.
        
        Args:
            method: RPC method name (e.g., "Bat.GetStatus")
            params: Parameters dictionary for the RPC call
            
        Returns:
            Response dictionary if successful, None otherwise
        """
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
            self._bind_socket_with_retry(sock)
            
            # Quick timeout to check if bytes are arriving (non-blocking)
            sock.settimeout(self.socket_timeout)

            for send_attempt in range(1, self.max_send_attempts + 1):
                rpc_id = random.randint(1000, 65000)
                req = {
                    "id": rpc_id,
                    "method": method,
                    "params": params
                }

                message = json.dumps(req).encode('utf-8')
                _LOGGER.info("REQUEST (attempt %d/%d): %s", send_attempt, self.max_send_attempts, message.decode('utf-8'))

                # Send the command
                sock.sendto(message, (self.device_ip, self.remote_port))
                
                # Wait for the complete response
                start_time = time.time()
                success, response_obj, response_data = await self._wait_for_response(sock, rpc_id, method, start_time)
                
                if success:
                    return response_obj
                
                # Log timeout details - use debug for retries, warning only on final failure
                elapsed_ms = (time.time() - start_time) * 1000
                is_final_attempt = (send_attempt == self.max_send_attempts)
                log_level = _LOGGER.warning if is_final_attempt else _LOGGER.debug
                
                if response_data:
                    log_level("Incomplete response after %.0fms (attempt %d/%d): %s", 
                             elapsed_ms, send_attempt, self.max_send_attempts, response_data)
                else:
                    log_level("No response after %.0fms (attempt %d/%d)", 
                             elapsed_ms, send_attempt, self.max_send_attempts)
                
                # Retry if we haven't exhausted attempts
                if send_attempt < self.max_send_attempts:
                    await asyncio.sleep(self.retry_delay)
                
            _LOGGER.warning("No valid response after %d attempts", self.max_send_attempts)
            return None
            
        except Exception as e:
            _LOGGER.error("Error sending %s request: %s", method, e)
            return None
        finally:
            if sock:
                sock.close()
        
    async def get_device_info(self, ble_mac: str) -> Optional[dict]:
        """
        Get device information by BLE MAC address.
        
        Args:
            ble_mac: BLE MAC address of the device
            
        Returns:
            Device information dictionary if successful, None otherwise
        """
        params = {"ble_mac": ble_mac}
        return await self._send_rpc_request("Marstek.GetDevice", params)
    
    async def get_battery_status(self, device_id: int) -> Optional[dict]:
        """
        Get battery status for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Battery status dictionary if successful, None otherwise
        """
        params = {"id": device_id}
        return await self._send_rpc_request("Bat.GetStatus", params)
    
    async def get_mode_status(self, device_id: int) -> Optional[dict]:
        """
        Get mode status for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Mode status dictionary if successful, None otherwise
        """
        params = {"id": device_id}
        return await self._send_rpc_request("ES.GetMode", params)
    
    async def get_em_status(self, device_id: int) -> Optional[dict]:
        """
        Get energy management status for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            EM status dictionary if successful, None otherwise
        """
        params = {"id": device_id}
        return await self._send_rpc_request("EM.GetStatus", params)
    
    async def get_wifi_status(self, device_id: int) -> Optional[dict]:
        """
        Get WiFi status for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            WiFi status dictionary if successful, None otherwise
        """
        params = {"id": device_id}
        return await self._send_rpc_request("Wifi.GetStatus", params)
    
    async def get_ble_status(self, device_id: int) -> Optional[dict]:
        """
        Get BLE status for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            BLE status dictionary if successful, None otherwise
        """
        params = {"id": device_id}
        return await self._send_rpc_request("BLE.GetStatus", params)