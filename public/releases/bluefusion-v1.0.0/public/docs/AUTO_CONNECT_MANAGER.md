# Auto-Connect Manager Implementation Guide

## Overview

The Auto-Connect Manager is a comprehensive BLE connection management system that handles automatic retries, connection stability monitoring, and advanced health checking for BlueFusion. It provides a robust solution for maintaining stable BLE connections in challenging environments.

## Features

### Core Functionality
- **Automatic Connection Retry**: Configurable retry strategies with exponential, linear, or fixed interval backoff
- **Connection Stability Monitoring**: Real-time metrics tracking including success rate, average connection time, and uptime
- **Active Health Checking**: Proactive connection verification using GATT characteristic reads
- **Automatic Reconnection**: Seamless reconnection on unexpected disconnections
- **Priority Management**: HIGH/MEDIUM/LOW priority levels for connection scheduling
- **Connection Limits**: Configurable maximum concurrent connections with automatic queueing

### Advanced Features
- **State Persistence**: Save and restore connection states between sessions
- **Analytics & Reporting**: Comprehensive health scoring and recommendations
- **Event System**: Flexible event-based architecture for monitoring
- **WebSocket Support**: Real-time status updates for web clients
- **Pause/Resume**: Temporarily disable problematic devices

## Architecture

### Components

1. **AutoConnectManager**: Main orchestrator class
   - Manages multiple device connections
   - Handles priority scheduling and connection limits
   - Provides analytics and reporting

2. **ManagedConnection**: Per-device connection state
   - Tracks retry attempts and connection metrics
   - Implements retry delay calculations
   - Maintains connection health data

3. **ConnectionConfig**: Configuration dataclass
   - Retry strategies and parameters
   - Timeout and health check intervals
   - Priority and connection limits

4. **ConnectionMetrics**: Metrics tracking
   - Success/failure counts
   - Connection timing statistics
   - Stability scoring

## Usage Examples

### Basic Usage

```python
from src.interfaces.auto_connect_manager import AutoConnectManager, ConnectionConfig
from src.interfaces.macbook_ble import MacBookBLE

# Initialize BLE interface
ble = MacBookBLE()
await ble.initialize()

# Create Auto-Connect Manager
manager = AutoConnectManager(ble)

# Add devices to manage
manager.add_managed_device("AA:BB:CC:DD:EE:FF")

# Start the manager
await manager.start()

# Get connection status
status = manager.get_connection_status("AA:BB:CC:DD:EE:FF")
print(f"Connection state: {status['state']}")
```

### Custom Configuration

```python
from src.interfaces.auto_connect_manager import ConnectionConfig, RetryStrategy, ConnectionPriority

# Configure for unreliable device
config = ConnectionConfig(
    max_retries=10,
    initial_retry_delay=2.0,
    max_retry_delay=120.0,
    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    connection_timeout=30.0,
    health_check_interval=15.0,
    priority=ConnectionPriority.HIGH,
    max_consecutive_failures=5
)

manager.add_managed_device("AA:BB:CC:DD:EE:FF", config)
```

### Event Monitoring

```python
def on_connection_event(address: str, event_type: str, data: dict):
    print(f"[{address}] {event_type}: {data}")

manager.register_event_callback(on_connection_event)
```

### Analytics Report

```python
# Generate comprehensive analytics
report = manager.generate_analytics_report()

print(f"Overall Success Rate: {report['overall_metrics']['average_success_rate']:.2%}")
print(f"Average Connection Time: {report['overall_metrics']['average_connection_time']:.2f}s")

# Device health scores
for address, analytics in report['device_analytics'].items():
    print(f"{address}: Health Score {analytics['health_score']:.1f}/100")
    for rec in analytics['recommendations']:
        print(f"  - {rec}")
```

## API Endpoints

The Auto-Connect Manager is integrated with the FastAPI server:

### REST API
- `POST /auto-connect/add` - Add device to auto-connect
- `DELETE /auto-connect/remove/{address}` - Remove device
- `POST /auto-connect/enable/{address}` - Enable device
- `POST /auto-connect/disable/{address}` - Disable device
- `POST /auto-connect/pause/{address}` - Pause device
- `GET /auto-connect/status/{address}` - Get device status
- `GET /auto-connect/status` - Get all device statuses
- `GET /auto-connect/analytics` - Get analytics report

### WebSocket
- Connect to `/ws` for real-time updates
- Events: `connection_success`, `connection_failed`, `health_check_success`, etc.

## Configuration Options

### Retry Strategies
1. **EXPONENTIAL_BACKOFF**: Delay doubles after each failure (1s, 2s, 4s, 8s...)
2. **LINEAR_BACKOFF**: Delay increases linearly (1s, 2s, 3s, 4s...)
3. **FIXED_INTERVAL**: Constant delay between retries

### Health Scoring Algorithm
The health score (0-100) is calculated based on:
- **Success Rate** (40% weight): Percentage of successful connections
- **Connection Time** (20% weight): Speed of establishing connections
- **Consecutive Failures** (20% weight): Recent failure patterns
- **Uptime** (20% weight): Duration of stable connections

### State Persistence
Connection states are saved to `~/.bluefusion/auto_connect_state.json`:
- Device configurations
- Connection metrics
- Enabled/disabled states
- Last known connection states

## Best Practices

1. **Priority Assignment**
   - Use HIGH priority for critical devices
   - Use MEDIUM for regular monitoring
   - Use LOW for optional/backup devices

2. **Retry Configuration**
   - Exponential backoff for unreliable networks
   - Fixed interval for predictable environments
   - Adjust max_retries based on device importance

3. **Health Monitoring**
   - Set appropriate health_check_interval (30s default)
   - Monitor health scores for early problem detection
   - Act on recommendations to improve stability

4. **Connection Limits**
   - Set max_concurrent_connections based on hardware
   - Consider BLE adapter limitations
   - Account for system resource constraints

## Troubleshooting

### Common Issues

1. **Devices stuck in FAILED state**
   - Check if device is in range
   - Verify device is advertising
   - Try pausing and resuming the device

2. **Poor health scores**
   - Review recommendations in analytics report
   - Adjust timeout and retry parameters
   - Check for interference or signal issues

3. **Connection queue not processing**
   - Verify connection limits are appropriate
   - Check if higher priority devices are blocking
   - Ensure failed devices aren't consuming slots

## Future Enhancements

Planned improvements include:
- Machine learning for adaptive retry strategies
- Predictive failure detection
- Multi-adapter support for increased capacity
- Cloud-based connection orchestration
- Integration with device fingerprinting

## File Locations

- **Implementation**: `/src/interfaces/auto_connect_manager.py`
- **Tests**: `/tests/test_auto_connect_manager.py`
- **Demo**: `/examples/auto_connect_demo.py`
- **API Integration**: `/src/api/fastapi_server.py`
- **State File**: `~/.bluefusion/auto_connect_state.json`