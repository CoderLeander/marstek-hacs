#!/usr/bin/env python3
"""
Standalone test script for Marstek UDP communication.
Use this to test your device connection outside of Home Assistant.
"""

import asyncio
import socket
import json
import random
import sys

class MarstekUDPTester:
    def __init__(self, device_ip: str, remote_port: int = 30000, local_port: int = 30000):
        self.device_ip = device_ip
        self.remote_port = remote_port
        self.local_port = local_port
    
    def test_raw_udp(self):
        """Test basic UDP connectivity."""
        print(f"Testing raw UDP connection to {self.device_ip}:{self.remote_port}")
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(5)
            
            # Send a simple test message
            test_message = b"PING"
            print(f"Sending: {test_message}")
            sock.sendto(test_message, (self.device_ip, self.remote_port))
            
            # Try to receive response
            try:
                response, addr = sock.recvfrom(1024)
                print(f"Received from {addr}: {response}")
                return True
            except socket.timeout:
                print("No response received (timeout)")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if sock:
                sock.close()
    
    def test_json_rpc(self, method: str, params: dict):
        """Test JSON-RPC communication."""
        print(f"Testing JSON-RPC: {method} with params {params}")
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.local_port))
            sock.settimeout(5)
            
            # Create JSON-RPC request
            rpc_id = random.randint(1000, 65000)
            req = {
                "id": rpc_id,
                "method": method,
                "params": params
            }
            
            message = json.dumps(req, separators=(',', ':')).encode('utf-8')
            print(f"Sending JSON-RPC: {message.decode('utf-8')}")
            
            sock.sendto(message, (self.device_ip, self.remote_port))
            
            # Wait for response
            try:
                response, addr = sock.recvfrom(4096)
                txt = response.decode('utf-8')
                print(f"Received JSON response: {txt}")
                
                try:
                    obj = json.loads(txt)
                    return obj
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    return None
                    
            except socket.timeout:
                print("No JSON-RPC response received (timeout)")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            if sock:
                sock.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_marstek_udp.py <device_ip> [ble_mac]")
        print("Example: python test_marstek_udp.py 192.168.1.100 AA:BB:CC:DD:EE:FF")
        return
    
    device_ip = sys.argv[1]
    ble_mac = sys.argv[2] if len(sys.argv) > 2 else "00:00:00:00:00:00"
    
    print(f"Testing Marstek device at {device_ip}")
    print(f"BLE MAC: {ble_mac}")
    print("-" * 50)
    
    tester = MarstekUDPTester(device_ip)
    
    # Test 1: Raw UDP
    print("1. Testing raw UDP connectivity...")
    raw_success = tester.test_raw_udp()
    print(f"Raw UDP test: {'PASS' if raw_success else 'FAIL'}")
    print()
    
    # Test 2: Try various JSON-RPC methods
    methods_to_try = [
        ("ping", {}),
        ("status", {}),
        ("hello", {}),
        ("info", {}),
        ("get_status", {}),
        ("device_info", {}),
        ("Marstek.GetDevice", {"ble_mac": ble_mac}),
        ("GetDevice", {"ble_mac": ble_mac}),
        ("get_device_info", {"ble_mac": ble_mac}),
        ("device_info", {"mac": ble_mac}),
    ]
    
    print("2. Testing JSON-RPC methods...")
    successful_methods = []
    
    for method, params in methods_to_try:
        print(f"Testing {method}...")
        result = tester.test_json_rpc(method, params)
        if result is not None:
            print(f"✓ {method} succeeded!")
            successful_methods.append((method, params, result))
        else:
            print(f"✗ {method} failed")
        print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    print(f"Raw UDP: {'PASS' if raw_success else 'FAIL'}")
    print(f"Successful methods: {len(successful_methods)}")
    
    if successful_methods:
        print("\nWorking methods:")
        for method, params, result in successful_methods:
            print(f"  - {method}: {result}")
    else:
        print("\nNo methods worked. Check:")
        print("  - Device IP address is correct")
        print("  - Device is powered on and connected to network")
        print("  - No firewall blocking UDP port 30000")
        print("  - Device supports UDP communication")

if __name__ == "__main__":
    main()