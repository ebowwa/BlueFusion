#!/usr/bin/env python3
"""
Packet Analysis and Inspection wiki content
"""

CONTENT = """# BlueFusion Packet Analysis Guide

## Packet Inspector Overview

The BlueFusion Packet Inspector provides real-time analysis of BLE packets with advanced filtering and decoding capabilities.

## Packet Types

### Advertisement Packets
- **ADV_IND**: Connectable undirected advertising
- **ADV_DIRECT_IND**: Connectable directed advertising
- **ADV_SCAN_IND**: Scannable undirected advertising
- **ADV_NONCONN_IND**: Non-connectable undirected advertising
- **SCAN_RSP**: Scan response packets
- **CONNECT_REQ**: Connection request

### Data Packets
- **LL_DATA**: Link Layer data packets
- **LL_CONTROL**: Link Layer control packets
- **ATT_PDU**: Attribute Protocol PDUs
- **L2CAP**: Logical Link Control packets

## Packet Structure

### Basic Packet Format
```
┌─────────────┬──────────┬─────────┬─────────┐
│  Preamble   │  Access  │  PDU    │  CRC    │
│  (1 byte)   │  Address │ Header  │(3 bytes)│
│             │ (4 bytes)│(2 bytes)│         │
└─────────────┴──────────┴─────────┴─────────┘
```

### PDU Header Fields
- **PDU Type** (4 bits): Packet type identifier
- **RFU** (2 bits): Reserved for future use
- **TxAdd** (1 bit): Transmitter address type
- **RxAdd** (1 bit): Receiver address type
- **Length** (8 bits): Payload length

## Using the Packet Inspector

### Basic Filtering
```python
# Filter by device address
filter_config = {
    "address": "AA:BB:CC:DD:EE:FF",
    "direction": "both"  # "tx", "rx", or "both"
}

# Filter by packet type
filter_config = {
    "packet_types": ["ADV_IND", "SCAN_RSP"],
    "include_empty": False
}

# Filter by RSSI threshold
filter_config = {
    "min_rssi": -70,
    "max_rssi": -30
}
```

### Advanced Filtering
```python
# Complex filter with multiple criteria
complex_filter = {
    "addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"],
    "packet_types": ["ADV_IND", "SCAN_RSP", "LL_DATA"],
    "min_rssi": -80,
    "services": ["180A", "180F"],  # Filter by advertised services
    "manufacturer_id": "004C",  # Apple Inc.
    "name_pattern": ".*Sensor.*"  # Regex pattern for device names
}
```

## Packet Decoding

### Advertisement Data Decoding
```python
# Example decoded advertisement
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "address": "AA:BB:CC:DD:EE:FF",
    "address_type": "random",
    "rssi": -65,
    "packet_type": "ADV_IND",
    "data": {
        "flags": ["LE General Discoverable", "BR/EDR Not Supported"],
        "name": "BlueSensor-001",
        "services": ["180A", "180F", "181A"],
        "manufacturer_data": {
            "company_id": "004C",
            "data": "0215....",
            "decoded": "iBeacon: UUID=..., Major=1, Minor=2"
        },
        "tx_power": -59,
        "service_data": {
            "180F": "64",  # Battery level 100%
            "decoded": {"battery_level": 100}
        }
    }
}
```

### GATT Data Decoding
```python
# Example GATT read response
{
    "timestamp": "2024-01-15T10:31:00.456Z",
    "connection_handle": "0x0040",
    "packet_type": "ATT_READ_RSP",
    "data": {
        "attribute_handle": "0x0025",
        "value": "426C756546757369",
        "decoded": {
            "service": "180A",  # Device Information
            "characteristic": "2A29",  # Manufacturer Name
            "value": "BlueFusion",
            "encoding": "UTF-8"
        }
    }
}
```

## Protocol Analysis

### Link Layer Analysis
```python
# Connection parameters
{
    "connection_interval": "7.5ms",
    "slave_latency": 0,
    "supervision_timeout": "100ms",
    "hop_increment": 5,
    "channel_map": "0x1FFFFFFFFF",  # All 37 channels
    "crc_init": "0x123456"
}
```

### Security Analysis
```python
# Pairing information
{
    "pairing_method": "Just Works",
    "io_capabilities": "NoInputNoOutput",
    "authentication": "No MITM Protection",
    "encryption": "AES-CCM",
    "key_size": 16,
    "ltk_present": true,
    "irk_present": false,
    "csrk_present": false
}
```

## Real-time Analysis Features

### Packet Rate Analysis
```python
# Monitor packet rates
packet_stats = {
    "total_packets": 15234,
    "packets_per_second": 125.5,
    "by_type": {
        "ADV_IND": 8500,
        "SCAN_RSP": 4200,
        "LL_DATA": 2534
    },
    "by_device": {
        "AA:BB:CC:DD:EE:FF": 5000,
        "11:22:33:44:55:66": 3234
    }
}
```

### Channel Analysis
```python
# Channel utilization
channel_stats = {
    "channel_37": {"packets": 5100, "utilization": "34%"},
    "channel_38": {"packets": 5067, "utilization": "33%"},
    "channel_39": {"packets": 5067, "utilization": "33%"},
    "data_channels": {
        "active": [0, 5, 10, 15, 20, 25, 30, 35],
        "blocked": [11, 12, 13]  # WiFi interference
    }
}
```

## Export and Analysis

### Export Formats

#### PCAP Export
```python
# Export to Wireshark-compatible format
export_config = {
    "format": "pcap",
    "include_metadata": true,
    "timestamp_format": "absolute"
}
```

#### JSON Export
```python
# Export for further analysis
export_config = {
    "format": "json",
    "pretty_print": true,
    "include_raw": true,
    "include_decoded": true
}
```

#### CSV Export
```python
# Export for spreadsheet analysis
export_config = {
    "format": "csv",
    "fields": ["timestamp", "address", "rssi", "packet_type", "data"],
    "delimiter": ","
}
```

### Analysis Scripts

#### Timing Analysis
```python
# Analyze connection intervals
def analyze_connection_timing(packets):
    intervals = []
    last_timestamp = None
    
    for packet in packets:
        if packet['type'] == 'LL_DATA':
            if last_timestamp:
                interval = packet['timestamp'] - last_timestamp
                intervals.append(interval)
            last_timestamp = packet['timestamp']
    
    return {
        "average_interval": np.mean(intervals),
        "std_deviation": np.std(intervals),
        "min_interval": min(intervals),
        "max_interval": max(intervals)
    }
```

#### Advertisement Analysis
```python
# Analyze advertisement patterns
def analyze_advertisements(packets):
    devices = {}
    
    for packet in packets:
        if packet['type'] in ['ADV_IND', 'ADV_NONCONN_IND']:
            addr = packet['address']
            if addr not in devices:
                devices[addr] = {
                    'count': 0,
                    'rssi_values': [],
                    'intervals': [],
                    'last_seen': None
                }
            
            devices[addr]['count'] += 1
            devices[addr]['rssi_values'].append(packet['rssi'])
            
            if devices[addr]['last_seen']:
                interval = packet['timestamp'] - devices[addr]['last_seen']
                devices[addr]['intervals'].append(interval)
            
            devices[addr]['last_seen'] = packet['timestamp']
    
    return devices
```

## Troubleshooting Packet Analysis

### Missing Packets
- Check interface configuration
- Verify channel hopping settings
- Increase buffer size for high-traffic scenarios
- Check for USB bandwidth limitations (sniffer)

### Decoding Errors
- Update protocol parsers
- Check for proprietary protocols
- Verify packet integrity (CRC errors)
- Enable raw packet logging

### Performance Issues
- Enable packet filtering at interface level
- Reduce visualization update rate
- Use binary export formats
- Implement sampling for high-volume captures
"""