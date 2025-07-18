"""
Auto-Connect Manager for BlueFusion
Handles connection retries, stability monitoring, and automatic reconnection
"""

import asyncio
import time
import json
import os
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
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


class ConnectionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


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
    priority: ConnectionPriority = ConnectionPriority.MEDIUM
    max_concurrent_connections: int = 5


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
    
    def __init__(self, ble_interface: BLEInterface, default_config: Optional[ConnectionConfig] = None, 
                 state_file: Optional[str] = None):
        self.ble_interface = ble_interface
        self.default_config = default_config or ConnectionConfig()
        self.managed_connections: Dict[str, ManagedConnection] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.stability_monitor_task: Optional[asyncio.Task] = None
        self.event_callbacks: List[Callable[[str, str, Dict[str, Any]], None]] = []
        self._running = False
        self.state_file = state_file or os.path.join(os.path.expanduser("~"), ".bluefusion", "auto_connect_state.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        # Register for BLE interface events
        self.ble_interface.register_callback(self._on_ble_event)
        
        # Load saved state
        self._load_state()
    
    def add_managed_device(self, address: str, config: Optional[ConnectionConfig] = None):
        """Add a device to be managed by the auto-connect manager"""
        device_config = config or self.default_config
        self.managed_connections[address] = ManagedConnection(address, device_config)
        
        self._emit_event(address, "device_added", {"config": device_config.__dict__})
        
        # Save state after adding device
        if self._running:
            self._save_state()
    
    def remove_managed_device(self, address: str):
        """Remove a device from management"""
        if address in self.managed_connections:
            # Cancel any ongoing connection task
            if address in self.connection_tasks:
                self.connection_tasks[address].cancel()
                del self.connection_tasks[address]
            
            del self.managed_connections[address]
            self._emit_event(address, "device_removed", {})
            
            # Save state after removing device
            if self._running:
                self._save_state()
    
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
        
        # Start periodic state saving
        self.state_save_task = asyncio.create_task(self.save_state_periodically())
        
        # Start connection tasks for all managed devices, respecting priority
        await self._start_priority_connections()
    
    async def stop(self):
        """Stop the auto-connect manager"""
        self._running = False
        
        # Save final state
        self._save_state()
        
        # Cancel all connection tasks
        for task in self.connection_tasks.values():
            task.cancel()
        self.connection_tasks.clear()
        
        # Cancel stability monitor
        if self.stability_monitor_task:
            self.stability_monitor_task.cancel()
            
        # Cancel state save task
        if hasattr(self, 'state_save_task') and self.state_save_task:
            self.state_save_task.cancel()
    
    async def _start_priority_connections(self):
        """Start connection tasks based on priority and connection limits"""
        # Group devices by priority
        priority_groups = {
            ConnectionPriority.HIGH: [],
            ConnectionPriority.MEDIUM: [],
            ConnectionPriority.LOW: []
        }
        
        for address, connection in self.managed_connections.items():
            if connection.is_enabled:
                priority_groups[connection.config.priority].append(address)
        
        # Start connections in priority order
        active_connections = 0
        max_concurrent = self.default_config.max_concurrent_connections
        
        for priority in [ConnectionPriority.HIGH, ConnectionPriority.MEDIUM, ConnectionPriority.LOW]:
            for address in priority_groups[priority]:
                if active_connections >= max_concurrent:
                    # Wait for a connection slot to become available
                    self._emit_event(address, "connection_queued", {
                        "priority": priority.value,
                        "queue_position": active_connections - max_concurrent + 1
                    })
                else:
                    self.connection_tasks[address] = asyncio.create_task(self._connection_manager(address))
                    active_connections += 1
    
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
        
        try:
            # Perform active health check by reading a standard characteristic
            # Generic Access Profile - Device Name (0x2A00) is usually available
            health_check_char = "00002A00-0000-1000-8000-00805F9B34FB"
            
            # Try to read the characteristic with a short timeout
            start_time = time.time()
            try:
                await asyncio.wait_for(
                    self.ble_interface.read_characteristic(address, health_check_char),
                    timeout=5.0
                )
                response_time = time.time() - start_time
                
                # Update activity timestamp
                connection.last_activity = datetime.now()
                
                self._emit_event(address, "health_check_success", {
                    "response_time": response_time
                })
                
            except asyncio.TimeoutError:
                # Health check timed out
                self._emit_event(address, "health_check_timeout", {
                    "timeout": 5.0
                })
                # Mark as disconnected to trigger reconnection
                connection.state = ConnectionState.DISCONNECTED
                return
                
            except Exception as e:
                # Health check failed with error
                self._emit_event(address, "health_check_failed", {
                    "error": str(e)
                })
                # Mark as disconnected to trigger reconnection
                connection.state = ConnectionState.DISCONNECTED
                return
                
        except Exception as e:
            # Fallback to passive monitoring if active check setup fails
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
                    # Check if we can start any queued connections
                    asyncio.create_task(self._check_connection_queue())
                    # Restart connection task if needed
                    if address not in self.connection_tasks and connection.is_enabled:
                        self.connection_tasks[address] = asyncio.create_task(self._connection_manager(address))
    
    async def _check_connection_queue(self):
        """Check if any queued connections can be started"""
        # Count active connections
        active_count = sum(1 for conn in self.managed_connections.values() 
                          if conn.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING])
        
        max_concurrent = self.default_config.max_concurrent_connections
        
        if active_count < max_concurrent:
            # Find highest priority disconnected device
            best_candidate = None
            best_priority = None
            
            for address, connection in self.managed_connections.items():
                if (connection.is_enabled and 
                    connection.state == ConnectionState.DISCONNECTED and
                    address not in self.connection_tasks):
                    
                    if best_priority is None or self._compare_priority(connection.config.priority, best_priority) > 0:
                        best_candidate = address
                        best_priority = connection.config.priority
            
            if best_candidate:
                self.connection_tasks[best_candidate] = asyncio.create_task(self._connection_manager(best_candidate))
                self._emit_event(best_candidate, "connection_dequeued", {
                    "priority": best_priority.value
                })
    
    def _compare_priority(self, p1: ConnectionPriority, p2: ConnectionPriority) -> int:
        """Compare two priorities. Returns: 1 if p1 > p2, 0 if equal, -1 if p1 < p2"""
        priority_values = {
            ConnectionPriority.HIGH: 3,
            ConnectionPriority.MEDIUM: 2,
            ConnectionPriority.LOW: 1
        }
        return priority_values[p1] - priority_values[p2]
    
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
    
    def _save_state(self):
        """Save current state to persistent storage"""
        try:
            state_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "devices": {}
            }
            
            for address, connection in self.managed_connections.items():
                state_data["devices"][address] = {
                    "config": asdict(connection.config),
                    "metrics": connection.metrics.model_dump(),
                    "enabled": connection.is_enabled,
                    "last_state": connection.state.value
                }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            self._emit_event("manager", "state_saved", {"file": self.state_file})
            
        except Exception as e:
            self._emit_event("manager", "state_save_error", {"error": str(e)})
    
    def _load_state(self):
        """Load state from persistent storage"""
        try:
            if not os.path.exists(self.state_file):
                return
                
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            # Validate version
            if state_data.get("version") != "1.0":
                self._emit_event("manager", "state_version_mismatch", {"version": state_data.get("version")})
                return
                
            # Restore devices
            for address, device_data in state_data.get("devices", {}).items():
                try:
                    # Convert config dict back to ConnectionConfig
                    config_data = device_data["config"]
                    config_data["retry_strategy"] = RetryStrategy(config_data["retry_strategy"])
                    config_data["priority"] = ConnectionPriority(config_data["priority"])
                    
                    config = ConnectionConfig(**config_data)
                    
                    # Add device with saved config
                    self.add_managed_device(address, config)
                    
                    # Restore metrics
                    connection = self.managed_connections[address]
                    metrics_data = device_data["metrics"]
                    # Convert string dates back to datetime objects
                    if metrics_data.get("last_connected"):
                        metrics_data["last_connected"] = datetime.fromisoformat(metrics_data["last_connected"])
                    if metrics_data.get("last_failure"):
                        metrics_data["last_failure"] = datetime.fromisoformat(metrics_data["last_failure"])
                    
                    connection.metrics = ConnectionMetrics(**metrics_data)
                    
                    # Restore enabled state
                    connection.is_enabled = device_data.get("enabled", True)
                    
                except Exception as e:
                    self._emit_event(address, "state_restore_error", {"error": str(e)})
                    
            self._emit_event("manager", "state_loaded", {
                "file": self.state_file, 
                "device_count": len(state_data.get("devices", {}))
            })
            
        except FileNotFoundError:
            # No saved state, start fresh
            pass
        except Exception as e:
            self._emit_event("manager", "state_load_error", {"error": str(e)})
    
    async def save_state_periodically(self, interval: float = 300.0):
        """Periodically save state to persistent storage"""
        while self._running:
            await asyncio.sleep(interval)
            self._save_state()
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report for all connections"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_devices": len(self.managed_connections),
            "connection_states": {},
            "overall_metrics": {
                "total_attempts": 0,
                "total_successes": 0,
                "total_failures": 0,
                "average_success_rate": 0.0,
                "average_connection_time": 0.0,
                "total_uptime": 0.0
            },
            "device_analytics": {},
            "priority_distribution": {
                ConnectionPriority.HIGH.value: 0,
                ConnectionPriority.MEDIUM.value: 0,
                ConnectionPriority.LOW.value: 0
            },
            "retry_strategy_distribution": {},
            "health_status": {
                "healthy": 0,
                "unhealthy": 0,
                "degraded": 0
            }
        }
        
        # Count connection states
        for state in ConnectionState:
            report["connection_states"][state.value] = 0
        
        # Analyze each device
        for address, connection in self.managed_connections.items():
            # Update state counts
            report["connection_states"][connection.state.value] += 1
            
            # Update priority distribution
            report["priority_distribution"][connection.config.priority.value] += 1
            
            # Update retry strategy distribution
            strategy = connection.config.retry_strategy.value
            report["retry_strategy_distribution"][strategy] = report["retry_strategy_distribution"].get(strategy, 0) + 1
            
            # Aggregate metrics
            metrics = connection.metrics
            report["overall_metrics"]["total_attempts"] += metrics.total_attempts
            report["overall_metrics"]["total_successes"] += metrics.successful_connections
            report["overall_metrics"]["total_failures"] += metrics.failed_connections
            report["overall_metrics"]["total_uptime"] += metrics.connection_uptime
            
            # Device-specific analytics
            device_health = self._calculate_device_health(connection)
            report["device_analytics"][address] = {
                "state": connection.state.value,
                "metrics": metrics.model_dump(),
                "config": {
                    "priority": connection.config.priority.value,
                    "retry_strategy": connection.config.retry_strategy.value,
                    "max_retries": connection.config.max_retries
                },
                "health_score": device_health["score"],
                "health_status": device_health["status"],
                "recommendations": device_health["recommendations"]
            }
            
            # Update health status counts
            report["health_status"][device_health["status"]] += 1
        
        # Calculate overall averages
        if report["overall_metrics"]["total_attempts"] > 0:
            report["overall_metrics"]["average_success_rate"] = (
                report["overall_metrics"]["total_successes"] / 
                report["overall_metrics"]["total_attempts"]
            )
        
        # Calculate average connection time
        total_connection_time = sum(
            conn.metrics.average_connection_time * conn.metrics.successful_connections
            for conn in self.managed_connections.values()
            if conn.metrics.successful_connections > 0
        )
        total_successful = report["overall_metrics"]["total_successes"]
        if total_successful > 0:
            report["overall_metrics"]["average_connection_time"] = total_connection_time / total_successful
        
        return report
    
    def _calculate_device_health(self, connection: ManagedConnection) -> Dict[str, Any]:
        """Calculate health score and recommendations for a device"""
        health = {
            "score": 0.0,
            "status": "unhealthy",
            "recommendations": []
        }
        
        metrics = connection.metrics
        
        # Calculate health score (0-100)
        if metrics.total_attempts == 0:
            health["score"] = 50.0  # No data yet
        else:
            # Success rate (40% weight)
            success_rate = metrics.stability_score * 40
            
            # Connection time penalty (20% weight)
            if metrics.average_connection_time > 0:
                time_score = max(0, 20 - (metrics.average_connection_time - 2) * 2)
            else:
                time_score = 10
                
            # Consecutive failures penalty (20% weight)
            failure_penalty = max(0, 20 - metrics.consecutive_failures * 5)
            
            # Uptime bonus (20% weight)
            if metrics.connection_uptime > 0:
                uptime_score = min(20, metrics.connection_uptime / 300)  # 5 minutes = full score
            else:
                uptime_score = 0
                
            health["score"] = success_rate + time_score + failure_penalty + uptime_score
        
        # Determine status
        if health["score"] >= 80:
            health["status"] = "healthy"
        elif health["score"] >= 50:
            health["status"] = "degraded"
        else:
            health["status"] = "unhealthy"
            
        # Generate recommendations
        if metrics.stability_score < 0.5:
            health["recommendations"].append("Consider increasing retry attempts or timeout")
            
        if metrics.consecutive_failures >= 3:
            health["recommendations"].append("Device experiencing repeated failures - check signal strength")
            
        if metrics.average_connection_time > 5:
            health["recommendations"].append("Slow connection times - consider reducing connection timeout")
            
        if connection.state == ConnectionState.PAUSED:
            health["recommendations"].append("Device is paused - consider re-enabling if issues resolved")
            
        return health
    
    def get_connection_summary(self) -> str:
        """Get a human-readable summary of connection status"""
        states = {}
        for conn in self.managed_connections.values():
            states[conn.state.value] = states.get(conn.state.value, 0) + 1
            
        summary_parts = []
        summary_parts.append(f"Total devices: {len(self.managed_connections)}")
        
        for state, count in states.items():
            if count > 0:
                summary_parts.append(f"{state}: {count}")
                
        return " | ".join(summary_parts)