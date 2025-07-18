#!/usr/bin/env python3
"""
Test direct API calls to debug UI issues
"""
import sys
sys.path.insert(0, 'src')

from ui.client import BlueFusionClient
from ui.interface_handlers import InterfaceHandlers
from ui.websocket_handler import WebSocketHandler

print("Testing Direct API Calls")
print("=" * 50)

# Initialize components like the UI does
client = BlueFusionClient("http://localhost:8000")
ws_handler = WebSocketHandler("ws://localhost:8000/stream")
interface_handlers = InterfaceHandlers(client, ws_handler)

# Test 1: Get Interface Status
print("\n1. Testing get_interface_status()...")
try:
    status = interface_handlers.get_interface_status()
    print("Success! Status:")
    print(status)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Start Scanning
print("\n2. Testing start_scanning()...")
try:
    result = interface_handlers.start_scanning("Both", "Active")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Get devices
print("\n3. Testing get_devices()...")
try:
    devices = client.get_devices("both")
    print(f"Found {len(devices.get('macbook', []))} MacBook devices")
except Exception as e:
    print(f"Error: {e}")