"""
Unit tests for Auto-Connect Manager
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.interfaces.auto_connect_manager import (
    AutoConnectManager,
    ConnectionConfig,
    ConnectionState,
    RetryStrategy,
    ManagedConnection,
    ConnectionMetrics
)
from src.interfaces.base import BLEInterface, BLEPacket, DeviceType


class MockBLEInterface(BLEInterface):
    """Mock BLE interface for testing"""
    
    def __init__(self):
        super().__init__(DeviceType.MACBOOK_BLE)
        self.connect_results = {}
        self.connect_delays = {}
        self.connect_call_count = {}
        
    async def initialize(self):
        pass
        
    async def start_scanning(self, passive=False):
        pass
        
    async def stop_scanning(self):
        pass
        
    async def get_devices(self):
        return []
        
    async def connect(self, address: str, security_requirements=None) -> bool:
        self.connect_call_count[address] = self.connect_call_count.get(address, 0) + 1
        
        if address in self.connect_delays:
            await asyncio.sleep(self.connect_delays[address])
            
        return self.connect_results.get(address, False)
        
    async def disconnect(self, address: str):
        pass
        
    async def packet_stream(self):
        while True:
            yield BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address="test",
                rssi=-50,
                data=b"",
                packet_type="test"
            )
            await asyncio.sleep(1)
    
    async def discover_services(self, address: str):
        return []
    
    async def discover_characteristics(self, address: str, service_uuid: str):
        return []
    
    async def discover_descriptors(self, address: str, char_uuid: str):
        return []


class TestConnectionConfig:
    """Test ConnectionConfig class"""
    
    def test_default_config(self):
        config = ConnectionConfig()
        assert config.max_retries == 5
        assert config.initial_retry_delay == 1.0
        assert config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.reconnect_on_failure is True
        
    def test_custom_config(self):
        config = ConnectionConfig(
            max_retries=10,
            initial_retry_delay=2.0,
            retry_strategy=RetryStrategy.FIXED_INTERVAL
        )
        assert config.max_retries == 10
        assert config.initial_retry_delay == 2.0
        assert config.retry_strategy == RetryStrategy.FIXED_INTERVAL


class TestManagedConnection:
    """Test ManagedConnection class"""
    
    def test_initial_state(self):
        config = ConnectionConfig()
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        assert connection.address == "AA:BB:CC:DD:EE:FF"
        assert connection.state == ConnectionState.DISCONNECTED
        assert connection.retry_count == 0
        assert connection.is_enabled is True
        assert connection.metrics.total_attempts == 0
        
    def test_exponential_backoff_retry_delay(self):
        config = ConnectionConfig(
            initial_retry_delay=1.0,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        # Test exponential backoff
        assert connection.calculate_retry_delay() == 1.0
        connection.retry_count = 1
        assert connection.calculate_retry_delay() == 2.0
        connection.retry_count = 2
        assert connection.calculate_retry_delay() == 4.0
        connection.retry_count = 3
        assert connection.calculate_retry_delay() == 8.0
        
    def test_linear_backoff_retry_delay(self):
        config = ConnectionConfig(
            initial_retry_delay=2.0,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF
        )
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        # Test linear backoff
        assert connection.calculate_retry_delay() == 2.0
        connection.retry_count = 1
        assert connection.calculate_retry_delay() == 4.0
        connection.retry_count = 2
        assert connection.calculate_retry_delay() == 6.0
        
    def test_fixed_interval_retry_delay(self):
        config = ConnectionConfig(
            initial_retry_delay=5.0,
            retry_strategy=RetryStrategy.FIXED_INTERVAL
        )
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        # Test fixed interval
        assert connection.calculate_retry_delay() == 5.0
        connection.retry_count = 5
        assert connection.calculate_retry_delay() == 5.0
        
    def test_max_retry_delay_cap(self):
        config = ConnectionConfig(
            initial_retry_delay=1.0,
            max_retry_delay=10.0,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        connection.retry_count = 10  # Would normally be 1024 seconds
        assert connection.calculate_retry_delay() == 10.0
        
    def test_metrics_update_success(self):
        config = ConnectionConfig()
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        connection.update_metrics(True, 2.5)
        
        assert connection.metrics.total_attempts == 1
        assert connection.metrics.successful_connections == 1
        assert connection.metrics.failed_connections == 0
        assert connection.metrics.average_connection_time == 2.5
        assert connection.metrics.stability_score == 1.0
        assert connection.metrics.consecutive_failures == 0
        
    def test_metrics_update_failure(self):
        config = ConnectionConfig()
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        connection.update_metrics(False)
        
        assert connection.metrics.total_attempts == 1
        assert connection.metrics.successful_connections == 0
        assert connection.metrics.failed_connections == 1
        assert connection.metrics.stability_score == 0.0
        assert connection.metrics.consecutive_failures == 1
        
    def test_should_retry_logic(self):
        config = ConnectionConfig(max_retries=3, max_consecutive_failures=2)
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        # Should retry initially
        assert connection.should_retry() is True
        
        # Should not retry if disabled
        connection.is_enabled = False
        assert connection.should_retry() is False
        connection.is_enabled = True
        
        # Should not retry if max retries reached
        connection.retry_count = 3
        assert connection.should_retry() is False
        connection.retry_count = 0
        
        # Should not retry if max consecutive failures reached
        connection.metrics.consecutive_failures = 2
        assert connection.should_retry() is False
        
    def test_pause_functionality(self):
        config = ConnectionConfig()
        connection = ManagedConnection("AA:BB:CC:DD:EE:FF", config)
        
        # Pause for 5 seconds
        connection.pause(5.0)
        
        assert connection.state == ConnectionState.PAUSED
        assert connection.pause_until is not None
        assert connection.should_retry() is False


class TestAutoConnectManager:
    """Test AutoConnectManager class"""
    
    @pytest.fixture
    def mock_ble_interface(self):
        return MockBLEInterface()
        
    @pytest.fixture
    def manager(self, mock_ble_interface):
        return AutoConnectManager(mock_ble_interface)
        
    def test_initialization(self, manager):
        assert manager.ble_interface is not None
        assert manager.default_config is not None
        assert len(manager.managed_connections) == 0
        assert manager._running is False
        
    def test_add_managed_device(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        
        assert address in manager.managed_connections
        assert manager.managed_connections[address].address == address
        assert manager.managed_connections[address].is_enabled is True
        
    def test_add_managed_device_with_custom_config(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        config = ConnectionConfig(max_retries=10)
        manager.add_managed_device(address, config)
        
        assert manager.managed_connections[address].config.max_retries == 10
        
    def test_remove_managed_device(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        manager.remove_managed_device(address)
        
        assert address not in manager.managed_connections
        
    def test_enable_disable_device(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        
        manager.disable_device(address)
        assert manager.managed_connections[address].is_enabled is False
        
        manager.enable_device(address)
        assert manager.managed_connections[address].is_enabled is True
        
    def test_pause_device(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        
        manager.pause_device(address, 10.0)
        connection = manager.managed_connections[address]
        
        assert connection.state == ConnectionState.PAUSED
        assert connection.pause_until is not None
        
    def test_get_connection_status(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        
        status = manager.get_connection_status(address)
        
        assert status is not None
        assert status["address"] == address
        assert status["state"] == ConnectionState.DISCONNECTED.value
        assert status["enabled"] is True
        
    def test_get_all_connections_status(self, manager):
        addresses = ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
        for address in addresses:
            manager.add_managed_device(address)
            
        status = manager.get_all_connections_status()
        
        assert len(status) == 2
        for address in addresses:
            assert address in status
            assert status[address]["address"] == address
            
    def test_event_callback_registration(self, manager):
        callback_called = False
        callback_data = {}
        
        def test_callback(address: str, event_type: str, data: Dict[str, Any]):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = {"address": address, "event_type": event_type, "data": data}
            
        manager.register_event_callback(test_callback)
        manager.add_managed_device("AA:BB:CC:DD:EE:FF")
        
        assert callback_called is True
        assert callback_data["address"] == "AA:BB:CC:DD:EE:FF"
        assert callback_data["event_type"] == "device_added"
        
    @pytest.mark.anyio
    async def test_successful_connection_flow(self, manager, mock_ble_interface):
        address = "AA:BB:CC:DD:EE:FF"
        mock_ble_interface.connect_results[address] = True
        
        manager.add_managed_device(address)
        
        # Manually test connection attempt
        await manager._attempt_connection(address)
        
        connection = manager.managed_connections[address]
        assert connection.state == ConnectionState.CONNECTED
        assert connection.retry_count == 0
        assert connection.metrics.successful_connections == 1
        assert connection.metrics.total_attempts == 1
        
    @pytest.mark.anyio
    async def test_failed_connection_flow(self, manager, mock_ble_interface):
        address = "AA:BB:CC:DD:EE:FF"
        mock_ble_interface.connect_results[address] = False
        
        manager.add_managed_device(address)
        
        # Manually test connection attempt
        await manager._attempt_connection(address)
        
        connection = manager.managed_connections[address]
        assert connection.state == ConnectionState.FAILED
        assert connection.retry_count == 1
        assert connection.metrics.successful_connections == 0
        assert connection.metrics.failed_connections == 1
        
    @pytest.mark.anyio
    async def test_connection_timeout(self, manager, mock_ble_interface):
        address = "AA:BB:CC:DD:EE:FF"
        # Set a long delay to trigger timeout
        mock_ble_interface.connect_delays[address] = 5.0
        
        config = ConnectionConfig(connection_timeout=1.0)
        manager.add_managed_device(address, config)
        
        # Manually test connection attempt
        await manager._attempt_connection(address)
        
        connection = manager.managed_connections[address]
        assert connection.state == ConnectionState.FAILED
        assert connection.retry_count == 1
        
    @pytest.mark.anyio
    async def test_ble_event_handling(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        manager.add_managed_device(address)
        
        # Simulate connection event
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address=address,
            rssi=-50,
            data=b"",
            packet_type="connection"
        )
        
        manager._on_ble_event(packet)
        
        connection = manager.managed_connections[address]
        assert connection.state == ConnectionState.CONNECTED
        assert connection.retry_count == 0
        assert connection.last_activity is not None
        
    @pytest.mark.anyio
    async def test_disconnection_triggers_reconnect(self, manager):
        address = "AA:BB:CC:DD:EE:FF"
        config = ConnectionConfig(reconnect_on_failure=True)
        manager.add_managed_device(address, config)
        
        # Set connection to connected state
        connection = manager.managed_connections[address]
        connection.state = ConnectionState.CONNECTED
        
        # Simulate disconnection event
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address=address,
            rssi=-50,
            data=b"",
            packet_type="disconnection"
        )
        
        manager._on_ble_event(packet)
        
        # Should reset to disconnected state for reconnection
        assert connection.state == ConnectionState.DISCONNECTED
        assert connection.retry_count == 0
        
    @pytest.mark.anyio
    async def test_start_stop_manager(self, manager):
        # Test starting manager
        await manager.start()
        assert manager._running is True
        assert manager.stability_monitor_task is not None
        
        # Test stopping manager
        await manager.stop()
        assert manager._running is False
        assert len(manager.connection_tasks) == 0


if __name__ == "__main__":
    pytest.main([__file__])