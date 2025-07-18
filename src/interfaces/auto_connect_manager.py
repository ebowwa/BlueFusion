"""
Auto-Connect Manager for BlueFusion
Handles connection retries, stability monitoring, and automatic reconnection
"""

import asyncio
import time
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

from .base import BLEInterface, BLEDevice, BLEPacket, DeviceType
from .ble_errors import BLESecurityException, BLEPairingRequired


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    PAUSED = "paused"


class RetryStrategy(str, Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class ConnectionConfig:
    """Configuration for auto-connect behavior"""
    max_retries: int = 5
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    connection_timeout: float = 30.0
    stability_check_interval: float = 10.0
    reconnect_on_failure: bool = True
    health_check_interval: float = 30.0
    max_consecutive_failures: int = 3


class ConnectionMetrics(BaseModel):
    """Metrics for connection stability tracking"""
    total_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    last_connected: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    average_connection_time: float = 0.0
    connection_uptime: float = 0.0
    stability_score: float = 0.0
    consecutive_failures: int = 0


class ManagedConnection:
    """Represents a managed connection with retry logic and stability monitoring"""
    
    def __init__(self, address: str, config: ConnectionConfig):
        self.address = address
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.metrics = ConnectionMetrics()
        self.retry_count = 0
        self.connection_start_time: Optional[float] = None
        self.last_activity: Optional[datetime] = None
        self.is_enabled = True
        self.pause_until: Optional[datetime] = None
        
    def calculate_retry_delay(self) -> float:
        """Calculate delay before next retry attempt"""
        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.initial_retry_delay * (2 ** self.retry_count)
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.initial_retry_delay * (1 + self.retry_count)
        else:  # FIXED_INTERVAL
            delay = self.config.initial_retry_delay
            
        return min(delay, self.config.max_retry_delay)
    
    def update_metrics(self, success: bool, connection_time: Optional[float] = None):
        """Update connection metrics"""
        self.metrics.total_attempts += 1
        
        if success:
            self.metrics.successful_connections += 1
            self.metrics.last_connected = datetime.now()
            self.metrics.consecutive_failures = 0
            if connection_time:
                # Update average connection time
                total_time = self.metrics.average_connection_time * (self.metrics.successful_connections - 1)
                self.metrics.average_connection_time = (total_time + connection_time) / self.metrics.successful_connections
        else:
            self.metrics.failed_connections += 1
            self.metrics.last_failure = datetime.now()
            self.metrics.consecutive_failures += 1
            
        # Calculate stability score (successful connections / total attempts)
        self.metrics.stability_score = self.metrics.successful_connections / self.metrics.total_attempts
    
    def should_retry(self) -> bool:
        """Check if connection should be retried"""
        if not self.is_enabled:
            return False
            
        if self.pause_until and datetime.now() < self.pause_until:
            return False
            
        if self.retry_count >= self.config.max_retries:
            return False
            
        if self.metrics.consecutive_failures >= self.config.max_consecutive_failures:
            return False
            
        return True
    
    def pause(self, duration: float):
        """Pause reconnection attempts for a specified duration"""
        self.pause_until = datetime.now() + timedelta(seconds=duration)
        self.state = ConnectionState.PAUSED


class AutoConnectManager:
    """Manages automatic connection, reconnection, and stability monitoring"""
    
    def __init__(self, ble_interface: BLEInterface, default_config: Optional[ConnectionConfig] = None):
        self.ble_interface = ble_interface
        self.default_config = default_config or ConnectionConfig()
        self.managed_connections: Dict[str, ManagedConnection] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.stability_monitor_task: Optional[asyncio.Task] = None
        self.event_callbacks: List[Callable[[str, str, Dict[str, Any]], None]] = []
        self._running = False
        
        # Register for BLE interface events
        self.ble_interface.register_callback(self._on_ble_event)
    
    def add_managed_device(self, address: str, config: Optional[ConnectionConfig] = None):
        """Add a device to be managed by the auto-connect manager"""
        device_config = config or self.default_config
        self.managed_connections[address] = ManagedConnection(address, device_config)
        
        self._emit_event(address, "device_added", {"config": device_config.__dict__})
    
    def remove_managed_device(self, address: str):
        """Remove a device from management"""
        if address in self.managed_connections:
            # Cancel any ongoing connection task
            if address in self.connection_tasks:
                self.connection_tasks[address].cancel()
                del self.connection_tasks[address]
            
            del self.managed_connections[address]
            self._emit_event(address, "device_removed", {})
    
    def enable_device(self, address: str):
        """Enable auto-connect for a device"""
        if address in self.managed_connections:
            self.managed_connections[address].is_enabled = True
            self._emit_event(address, "device_enabled", {})
    
    def disable_device(self, address: str):
        """Disable auto-connect for a device"""
        if address in self.managed_connections:
            self.managed_connections[address].is_enabled = False
            # Cancel ongoing connection task
            if address in self.connection_tasks:
                self.connection_tasks[address].cancel()
                del self.connection_tasks[address]
            self._emit_event(address, "device_disabled", {})
    
    def pause_device(self, address: str, duration: float):
        """Pause auto-connect for a device for specified duration"""
        if address in self.managed_connections:
            self.managed_connections[address].pause(duration)
            self._emit_event(address, "device_paused", {"duration": duration})
    
    async def start(self):
        """Start the auto-connect manager"""
        self._running = True
        
        # Start stability monitoring
        self.stability_monitor_task = asyncio.create_task(self._stability_monitor())
        
        # Start connection tasks for all managed devices
        for address in self.managed_connections:
            if self.managed_connections[address].is_enabled:
                self.connection_tasks[address] = asyncio.create_task(self._connection_manager(address))
    
    async def stop(self):
        """Stop the auto-connect manager"""
        self._running = False
        
        # Cancel all connection tasks
        for task in self.connection_tasks.values():
            task.cancel()
        self.connection_tasks.clear()
        
        # Cancel stability monitor
        if self.stability_monitor_task:
            self.stability_monitor_task.cancel()
    
    async def _connection_manager(self, address: str):
        """Main connection management loop for a device"""
        connection = self.managed_connections[address]
        
        while self._running and connection.is_enabled:
            try:
                if connection.state == ConnectionState.DISCONNECTED:
                    if connection.should_retry():
                        await self._attempt_connection(address)
                    else:
                        # Max retries reached or device paused
                        await asyncio.sleep(connection.config.stability_check_interval)
                
                elif connection.state == ConnectionState.CONNECTED:
                    # Monitor connection health
                    await self._monitor_connection_health(address)
                
                elif connection.state == ConnectionState.FAILED:
                    # Wait before retrying
                    delay = connection.calculate_retry_delay()
                    await asyncio.sleep(delay)
                    connection.state = ConnectionState.DISCONNECTED
                
                elif connection.state == ConnectionState.PAUSED:
                    # Wait until pause expires
                    if connection.pause_until and datetime.now() >= connection.pause_until:
                        connection.pause_until = None
                        connection.state = ConnectionState.DISCONNECTED
                    else:
                        await asyncio.sleep(1.0)
                
                else:
                    await asyncio.sleep(1.0)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._emit_event(address, "manager_error", {"error": str(e)})
                await asyncio.sleep(5.0)
    
    async def _attempt_connection(self, address: str):
        """Attempt to connect to a device"""
        connection = self.managed_connections[address]
        connection.state = ConnectionState.CONNECTING
        connection.connection_start_time = time.time()
        
        self._emit_event(address, "connection_attempt", {"retry_count": connection.retry_count})
        
        try:
            # Attempt connection with timeout
            connected = await asyncio.wait_for(
                self.ble_interface.connect(address),
                timeout=connection.config.connection_timeout
            )
            
            connection_time = time.time() - connection.connection_start_time
            
            if connected:
                connection.state = ConnectionState.CONNECTED
                connection.retry_count = 0
                connection.last_activity = datetime.now()
                connection.update_metrics(True, connection_time)
                
                self._emit_event(address, "connection_success", {
                    "connection_time": connection_time,
                    "retry_count": connection.retry_count
                })
            else:
                connection.state = ConnectionState.FAILED
                connection.retry_count += 1
                connection.update_metrics(False)
                
                self._emit_event(address, "connection_failed", {
                    "retry_count": connection.retry_count,
                    "next_retry_delay": connection.calculate_retry_delay()
                })
                
        except asyncio.TimeoutError:
            connection.state = ConnectionState.FAILED
            connection.retry_count += 1
            connection.update_metrics(False)
            
            self._emit_event(address, "connection_timeout", {
                "retry_count": connection.retry_count,
                "timeout": connection.config.connection_timeout
            })
            
        except Exception as e:
            connection.state = ConnectionState.FAILED
            connection.retry_count += 1
            connection.update_metrics(False)
            
            self._emit_event(address, "connection_error", {
                "error": str(e),
                "retry_count": connection.retry_count
            })
    
    async def _monitor_connection_health(self, address: str):
        """Monitor the health of an active connection"""
        connection = self.managed_connections[address]
        
        # Check if connection is still active
        # This would typically involve checking if the BLE client is still connected
        # For now, we'll use a simple activity-based check
        
        if connection.last_activity:
            time_since_activity = datetime.now() - connection.last_activity
            if time_since_activity > timedelta(seconds=connection.config.health_check_interval * 2):
                # Connection appears stale, mark as disconnected
                connection.state = ConnectionState.DISCONNECTED
                self._emit_event(address, "connection_stale", {
                    "time_since_activity": time_since_activity.total_seconds()
                })
                return
        
        # Wait for next health check
        await asyncio.sleep(connection.config.health_check_interval)
    
    async def _stability_monitor(self):
        """Monitor overall connection stability"""
        while self._running:
            try:
                stability_report = {}
                
                for address, connection in self.managed_connections.items():
                    # Update uptime if connected
                    if connection.state == ConnectionState.CONNECTED and connection.connection_start_time:
                        uptime = time.time() - connection.connection_start_time
                        connection.metrics.connection_uptime = uptime
                    
                    stability_report[address] = {
                        "state": connection.state.value,
                        "metrics": connection.metrics.model_dump(),
                        "retry_count": connection.retry_count,
                        "enabled": connection.is_enabled
                    }
                
                self._emit_event("manager", "stability_report", stability_report)
                
                await asyncio.sleep(self.default_config.stability_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._emit_event("manager", "stability_error", {"error": str(e)})
                await asyncio.sleep(5.0)
    
    def _on_ble_event(self, packet: BLEPacket):
        """Handle BLE interface events"""
        address = packet.address
        
        if address in self.managed_connections:
            connection = self.managed_connections[address]
            connection.last_activity = datetime.now()
            
            # Handle connection/disconnection events
            if packet.packet_type == "connection":
                connection.state = ConnectionState.CONNECTED
                connection.retry_count = 0
                
            elif packet.packet_type == "disconnection":
                if connection.config.reconnect_on_failure:
                    connection.state = ConnectionState.DISCONNECTED
                    connection.retry_count = 0
                    # Restart connection task if needed
                    if address not in self.connection_tasks and connection.is_enabled:
                        self.connection_tasks[address] = asyncio.create_task(self._connection_manager(address))
    
    def register_event_callback(self, callback: Callable[[str, str, Dict[str, Any]], None]):
        """Register callback for auto-connect events"""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, address: str, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered callbacks"""
        for callback in self.event_callbacks:
            try:
                callback(address, event_type, data)
            except Exception as e:
                print(f"Event callback error: {e}")
    
    def get_connection_status(self, address: str) -> Optional[Dict[str, Any]]:
        """Get current status of a managed connection"""
        if address in self.managed_connections:
            connection = self.managed_connections[address]
            return {
                "address": address,
                "state": connection.state.value,
                "metrics": connection.metrics.model_dump(),
                "retry_count": connection.retry_count,
                "enabled": connection.is_enabled,
                "paused_until": connection.pause_until.isoformat() if connection.pause_until else None
            }
        return None
    
    def get_all_connections_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all managed connections"""
        return {
            address: self.get_connection_status(address) 
            for address in self.managed_connections
        }