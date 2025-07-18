#!/usr/bin/env python3
"""
Interface Configuration wiki content
"""

CONTENT = """# Interface Configuration

## MacBook Interface
The MacBook interface uses native macOS Core Bluetooth APIs:
- **Advantages**: No additional hardware required
- **Limitations**: Limited to advertising data only
- **Best for**: General device discovery and monitoring

## Sniffer Interface
The USB sniffer interface provides low-level packet capture:
- **Advantages**: Full packet capture, channel hopping, raw data access
- **Requirements**: Compatible USB BLE sniffer hardware
- **Best for**: Protocol analysis and debugging

## Channel Settings
- **Default Channel**: 37 (primary advertising channel)
- **Channel Range**: 0-39 (all BLE channels)
- **Recommendation**: Use channel 37-39 for advertising monitoring

## Scan Configuration
- **Interface**: Choose based on your monitoring needs
- **Mode**: Passive for stealth monitoring, Active for detailed discovery
- **Refresh Rate**: Adjust based on system performance
"""