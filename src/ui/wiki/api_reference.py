#!/usr/bin/env python3
"""
API Reference wiki content
"""

CONTENT = """# API Reference

## Core Endpoints

### Device Management
- `GET /devices/{interface}` - Get discovered devices
- `POST /scan/start` - Start BLE scanning
- `POST /scan/stop` - Stop BLE scanning
- `GET /status` - Get interface status

### Sniffer Controls
- `POST /sniffer/channel` - Set sniffer channel
- `GET /sniffer/status` - Get sniffer status

### Statistics
- `GET /statistics` - Get packet statistics
- `GET /statistics/devices` - Get device statistics

## WebSocket Endpoints
- `ws://localhost:8000/ws` - Real-time packet stream

## Data Models

### Device
```json
{
  "address": "AA:BB:CC:DD:EE:FF",
  "name": "Device Name",
  "rssi": -45,
  "tx_power": 4,
  "manufacturer": "Company",
  "services": [],
  "first_seen": "2024-01-01T00:00:00Z",
  "last_seen": "2024-01-01T00:00:00Z"
}
```

### Packet
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "address": "AA:BB:CC:DD:EE:FF",
  "rssi": -45,
  "packet_type": "ADV_IND",
  "data": "...",
  "channel": 37
}
```

## Configuration
- **API Base URL**: http://localhost:8000
- **WebSocket URL**: ws://localhost:8000/ws
- **UI Port**: 7860
"""