#!/usr/bin/env python3
"""
API Examples and Usage wiki content
"""

CONTENT = """# BlueFusion API Examples

## REST API Usage

### Basic Setup
```python
import requests
import json

# Base URL for API
BASE_URL = "http://localhost:8000"

# Check API status
response = requests.get(f"{BASE_URL}/")
print(response.json())
```

### Scanning Operations

#### Start Scanning
```python
# Start active scan on both interfaces
scan_config = {
    "interface": "both",
    "mode": "active",
    "duration": 30
}

response = requests.post(
    f"{BASE_URL}/scan/start",
    json=scan_config
)
print(response.json())
```

#### Stop Scanning
```python
response = requests.post(f"{BASE_URL}/scan/stop")
print(response.json())
```

### Device Operations

#### List Discovered Devices
```python
response = requests.get(f"{BASE_URL}/devices")
devices = response.json()

for device in devices:
    print(f"Device: {device['address']} - {device['name']} (RSSI: {device['rssi']})")
```

#### Connect to Device
```python
device_address = "AA:BB:CC:DD:EE:FF"
response = requests.post(f"{BASE_URL}/connect/{device_address}")
print(response.json())
```

#### Disconnect from Device
```python
response = requests.post(f"{BASE_URL}/disconnect/{device_address}")
print(response.json())
```

### Service Discovery

#### List Device Services
```python
response = requests.get(f"{BASE_URL}/device/{device_address}/services")
services = response.json()

for service in services:
    print(f"Service: {service['uuid']} - {service['description']}")
```

#### Read Characteristic
```python
service_uuid = "180A"  # Device Information Service
char_uuid = "2A29"     # Manufacturer Name

response = requests.get(
    f"{BASE_URL}/device/{device_address}/read",
    params={
        "service": service_uuid,
        "characteristic": char_uuid
    }
)
print(response.json())
```

### WebSocket Streaming

#### Real-time Packet Stream
```python
import websocket
import json

def on_message(ws, message):
    packet = json.loads(message)
    print(f"Packet from {packet['address']}: {packet['data']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

# Connect to WebSocket
ws = websocket.WebSocketApp(
    "ws://localhost:8000/stream",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# Start streaming
ws.run_forever()
```

### Advanced Examples

#### Packet Filtering
```python
# Configure packet filter
filter_config = {
    "addresses": ["AA:BB:CC:DD:EE:FF"],
    "min_rssi": -70,
    "packet_types": ["ADV_IND", "SCAN_RSP"]
}

response = requests.post(
    f"{BASE_URL}/filter/configure",
    json=filter_config
)
```

#### Batch Operations
```python
# Scan multiple channels
batch_scan = {
    "operations": [
        {"channel": 37, "duration": 10},
        {"channel": 38, "duration": 10},
        {"channel": 39, "duration": 10}
    ]
}

response = requests.post(
    f"{BASE_URL}/scan/batch",
    json=batch_scan
)
```

#### Export Captured Data
```python
# Export packets as JSON
response = requests.get(
    f"{BASE_URL}/export",
    params={"format": "json", "include_raw": True}
)

with open("ble_capture.json", "w") as f:
    json.dump(response.json(), f, indent=2)
```

## Error Handling

```python
try:
    response = requests.post(f"{BASE_URL}/scan/start")
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Details: {response.json()}")
except requests.exceptions.ConnectionError:
    print("Failed to connect to API server")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Authentication (if enabled)

```python
# Include API key in headers
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.get(
    f"{BASE_URL}/devices",
    headers=headers
)
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute for general endpoints
- 10 requests per minute for scan operations
- Unlimited WebSocket connections (subject to server capacity)

## Async Examples (Python 3.7+)

```python
import aiohttp
import asyncio

async def async_scan():
    async with aiohttp.ClientSession() as session:
        # Start scan
        async with session.post(f"{BASE_URL}/scan/start") as resp:
            print(await resp.json())
        
        # Wait for results
        await asyncio.sleep(5)
        
        # Get devices
        async with session.get(f"{BASE_URL}/devices") as resp:
            devices = await resp.json()
            print(f"Found {len(devices)} devices")

# Run async function
asyncio.run(async_scan())
```
"""