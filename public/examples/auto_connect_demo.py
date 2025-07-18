"""
Auto-Connect Manager Demo
Demonstrates how to use the Auto-Connect Manager for robust BLE connections
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime

from src.interfaces.macbook_ble import MacBookBLE
from src.interfaces.auto_connect_manager import (
    AutoConnectManager,
    ConnectionConfig,
    RetryStrategy,
    ConnectionState
)
from src.interfaces.security_manager import SecurityManager


class AutoConnectDemo:
    """Demo class for Auto-Connect Manager"""
    
    def __init__(self):
        self.ble_interface = None
        self.auto_connect_manager = None
        self.event_log = []
        
    async def setup(self):
        """Initialize the BLE interface and Auto-Connect Manager"""
        print("Setting up BLE interface and Auto-Connect Manager...")
        
        # Create BLE interface
        security_manager = SecurityManager()
        self.ble_interface = MacBookBLE(security_manager)
        await self.ble_interface.initialize()
        
        # Create custom configuration for different types of devices
        stable_device_config = ConnectionConfig(
            max_retries=3,
            initial_retry_delay=1.0,
            max_retry_delay=30.0,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            connection_timeout=15.0,
            reconnect_on_failure=True,
            health_check_interval=30.0,
            stability_check_interval=10.0,
            max_consecutive_failures=2
        )
        
        unreliable_device_config = ConnectionConfig(
            max_retries=10,
            initial_retry_delay=2.0,
            max_retry_delay=120.0,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            connection_timeout=30.0,
            reconnect_on_failure=True,
            health_check_interval=15.0,
            stability_check_interval=5.0,
            max_consecutive_failures=5
        )
        
        # Create Auto-Connect Manager
        self.auto_connect_manager = AutoConnectManager(
            self.ble_interface,
            default_config=stable_device_config
        )
        
        # Register event callback for monitoring
        self.auto_connect_manager.register_event_callback(self._on_auto_connect_event)
        
        print("Setup complete!")
        
    async def discover_and_add_devices(self):
        """Discover nearby devices and add them to auto-connect management"""
        print("\\nStarting device discovery...")
        
        # Start scanning for devices
        await self.ble_interface.start_scanning()
        
        # Scan for 10 seconds
        await asyncio.sleep(10)
        
        # Stop scanning
        await self.ble_interface.stop_scanning()
        
        # Get discovered devices
        devices = await self.ble_interface.get_devices()
        print(f"Discovered {len(devices)} devices")
        
        # Add some devices to auto-connect management
        for device in devices[:3]:  # Add first 3 devices
            print(f"Adding device to auto-connect: {device.address} ({device.name})")
            
            # Use different configs based on device name/characteristics
            if device.name and "stable" in device.name.lower():
                # This is a stable device, use default config
                self.auto_connect_manager.add_managed_device(device.address)
            else:
                # This might be an unreliable device, use custom config
                unreliable_config = ConnectionConfig(
                    max_retries=8,
                    initial_retry_delay=3.0,
                    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                    max_consecutive_failures=4
                )
                self.auto_connect_manager.add_managed_device(device.address, unreliable_config)
        
        print("Device discovery and addition complete!")
        
    async def demonstrate_connection_management(self):
        """Demonstrate various connection management features"""
        print("\\nStarting Auto-Connect Manager...")
        
        # Start the auto-connect manager
        await self.auto_connect_manager.start()
        
        # Monitor connections for 60 seconds
        print("Monitoring connections for 60 seconds...")
        
        for i in range(12):  # Check every 5 seconds for 60 seconds
            await asyncio.sleep(5)
            
            # Get current status
            status = self.auto_connect_manager.get_all_connections_status()
            
            print(f"\\n--- Status Update {i+1} ---")
            for address, connection_status in status.items():
                device_name = "Unknown"
                for device in await self.ble_interface.get_devices():
                    if device.address == address:
                        device_name = device.name or "Unknown"
                        break
                
                print(f"Device: {device_name} ({address})")
                print(f"  State: {connection_status['state']}")
                print(f"  Retry Count: {connection_status['retry_count']}")
                print(f"  Enabled: {connection_status['enabled']}")
                print(f"  Success Rate: {connection_status['metrics']['stability_score']:.2%}")
                print(f"  Total Attempts: {connection_status['metrics']['total_attempts']}")
                print(f"  Consecutive Failures: {connection_status['metrics']['consecutive_failures']}")
                
                # Demonstrate pause functionality
                if i == 4 and connection_status['state'] == 'failed':
                    print(f"  -> Pausing device for 20 seconds due to failures")
                    self.auto_connect_manager.pause_device(address, 20.0)
                
                # Demonstrate disable/enable functionality
                if i == 8 and connection_status['retry_count'] > 3:
                    print(f"  -> Temporarily disabling device due to high retry count")
                    self.auto_connect_manager.disable_device(address)
                elif i == 10 and not connection_status['enabled']:
                    print(f"  -> Re-enabling device")
                    self.auto_connect_manager.enable_device(address)
        
        print("\\nConnection monitoring complete!")
        
    async def demonstrate_manual_operations(self):
        """Demonstrate manual operations on managed connections"""
        print("\\nDemonstrating manual operations...")
        
        # Get a connected device for manual operations
        status = self.auto_connect_manager.get_all_connections_status()
        connected_device = None
        
        for address, connection_status in status.items():
            if connection_status['state'] == 'connected':
                connected_device = address
                break
        
        if connected_device:
            print(f"Performing manual operations on connected device: {connected_device}")
            
            # Try to read a characteristic (Device Name)
            device_name = await self.ble_interface.read_characteristic(
                connected_device, 
                "00002A00-0000-1000-8000-00805F9B34FB"  # Device Name characteristic
            )
            
            if device_name:
                print(f"Device Name: {device_name.decode('utf-8', errors='ignore')}")
            
            # Try to read manufacturer name
            manufacturer = await self.ble_interface.read_characteristic(
                connected_device,
                "00002A29-0000-1000-8000-00805F9B34FB"  # Manufacturer Name String
            )
            
            if manufacturer:
                print(f"Manufacturer: {manufacturer.decode('utf-8', errors='ignore')}")
                
        else:
            print("No connected devices available for manual operations")
            
    async def show_event_log(self):
        """Display the event log"""
        print("\\n=== Auto-Connect Event Log ===")
        
        for event in self.event_log[-20:]:  # Show last 20 events
            timestamp = event['timestamp'].strftime("%H:%M:%S")
            print(f"[{timestamp}] {event['address']}: {event['event_type']}")
            
            # Show relevant event data
            if event['event_type'] == 'connection_success':
                print(f"  -> Connected in {event['data'].get('connection_time', 0):.2f}s")
            elif event['event_type'] == 'connection_failed':
                print(f"  -> Failed, retry {event['data'].get('retry_count', 0)}")
            elif event['event_type'] == 'connection_timeout':
                print(f"  -> Timeout after {event['data'].get('timeout', 0)}s")
            elif event['event_type'] == 'stability_report':
                print(f"  -> Stability report generated")
    
    async def show_analytics_report(self):
        """Display comprehensive analytics report"""
        print("\\n=== Connection Analytics Report ===")
        
        report = self.auto_connect_manager.generate_analytics_report()
        
        # Overall summary
        print(f"\\nTimestamp: {report['timestamp']}")
        print(f"Total Devices: {report['total_devices']}")
        
        # Connection states
        print("\\nConnection States:")
        for state, count in report['connection_states'].items():
            if count > 0:
                print(f"  {state}: {count}")
        
        # Overall metrics
        metrics = report['overall_metrics']
        print("\\nOverall Metrics:")
        print(f"  Total Attempts: {metrics['total_attempts']}")
        print(f"  Success Rate: {metrics['average_success_rate']:.2%}")
        print(f"  Average Connection Time: {metrics['average_connection_time']:.2f}s")
        print(f"  Total Uptime: {metrics['total_uptime']:.0f}s")
        
        # Priority distribution
        print("\\nPriority Distribution:")
        for priority, count in report['priority_distribution'].items():
            if count > 0:
                print(f"  {priority}: {count}")
        
        # Health status
        print("\\nHealth Status:")
        for status, count in report['health_status'].items():
            if count > 0:
                print(f"  {status}: {count}")
        
        # Device-specific details
        print("\\nDevice Analytics:")
        for address, analytics in report['device_analytics'].items():
            print(f"\\n  Device: {address}")
            print(f"    State: {analytics['state']}")
            print(f"    Health Score: {analytics['health_score']:.1f}/100")
            print(f"    Health Status: {analytics['health_status']}")
            if analytics['recommendations']:
                print("    Recommendations:")
                for rec in analytics['recommendations']:
                    print(f"      - {rec}")
        
        # Connection summary
        print(f"\\nSummary: {self.auto_connect_manager.get_connection_summary()}")
                
    async def cleanup(self):
        """Clean up resources"""
        print("\\nCleaning up...")
        
        if self.auto_connect_manager:
            await self.auto_connect_manager.stop()
            
        if self.ble_interface:
            await self.ble_interface.stop_scanning()
            
        print("Cleanup complete!")
        
    def _on_auto_connect_event(self, address: str, event_type: str, data: Dict[str, Any]):
        """Handle auto-connect events"""
        event = {
            'timestamp': datetime.now(),
            'address': address,
            'event_type': event_type,
            'data': data
        }
        
        self.event_log.append(event)
        
        # Print important events immediately
        if event_type in ['connection_success', 'connection_failed', 'connection_timeout']:
            timestamp = event['timestamp'].strftime("%H:%M:%S")
            print(f"[{timestamp}] {address}: {event_type}")


async def main():
    """Main demo function"""
    demo = AutoConnectDemo()
    
    try:
        print("=== BlueFusion Auto-Connect Manager Demo ===")
        print("This demo shows how to use the Auto-Connect Manager for robust BLE connections")
        print("with automatic retry logic, connection stability monitoring, and reconnection.")
        print()
        
        # Setup
        await demo.setup()
        
        # Discover and add devices
        await demo.discover_and_add_devices()
        
        # Demonstrate connection management
        await demo.demonstrate_connection_management()
        
        # Manual operations
        await demo.demonstrate_manual_operations()
        
        # Show event log
        await demo.show_event_log()
        
        # Show analytics report
        await demo.show_analytics_report()
        
        print("\\n=== Demo Complete ===")
        print("The Auto-Connect Manager provides:")
        print("- Automatic connection retry with configurable strategies")
        print("- Connection stability monitoring and metrics")
        print("- Automatic reconnection on connection loss")
        print("- Pause/resume functionality for problematic devices")
        print("- Comprehensive event logging and monitoring")
        print("- Per-device configuration for different connection requirements")
        print("- Priority-based connection management")
        print("- Active health checking with probing")
        print("- Persistent state storage")
        print("- Advanced analytics and health reporting")
        
    except KeyboardInterrupt:
        print("\\nDemo interrupted by user")
    except Exception as e:
        print(f"\\nDemo error: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())