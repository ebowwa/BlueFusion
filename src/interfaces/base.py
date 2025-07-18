"""
Base classes and data models for BLE interfaces

All core data models (BLEDevice, BLEPacket, etc.) are defined here
to avoid duplication and ensure consistency across the project.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional, List, Callable
from datetime import datetime
from pydantic import BaseModel
import asyncio
from enum import Enum
from .security_manager import SecurityManager, SecurityRequirements, SecurityLevel
from .ble_errors import BLESecurityException, BLEPairingRequired


class DeviceType(str, Enum):
    MACBOOK_BLE = "macbook_ble"
    SNIFFER_DONGLE = "sniffer_dongle"


class BLEPacket(BaseModel):
    timestamp: datetime
    source: DeviceType
    address: str
    rssi: int
    data: bytes
    packet_type: str
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


class BLEDescriptor(BaseModel):
    uuid: str
    handle: Optional[int] = None
    value: Optional[bytes] = None
    
    class Config:
        arbitrary_types_allowed = True


class BLECharacteristic(BaseModel):
    uuid: str
    handle: Optional[int] = None
    properties: List[str] = []
    value: Optional[bytes] = None
    descriptors: List[BLEDescriptor] = []
    
    class Config:
        arbitrary_types_allowed = True


class BLEService(BaseModel):
    uuid: str
    handle: Optional[int] = None
    primary: bool = True
    characteristics: List[BLECharacteristic] = []
    
    class Config:
        arbitrary_types_allowed = True


class BLEDevice(BaseModel):
    address: str
    name: Optional[str] = None
    rssi: int
    manufacturer_data: Optional[Dict[int, bytes]] = None
    service_data: Optional[Dict[str, bytes]] = None
    services: List[str] = []
    raw_data: Optional[bytes] = None
    discovered_services: List[BLEService] = []


class BLEInterface(ABC):
    def __init__(self, device_type: DeviceType, security_manager: Optional[SecurityManager] = None):
        self.device_type = device_type
        self._callbacks: List[Callable[[BLEPacket], None]] = []
        self._running = False
        self.security_manager = security_manager or SecurityManager()
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the BLE interface"""
        pass
    
    @abstractmethod
    async def start_scanning(self, passive: bool = False) -> None:
        """Start BLE scanning"""
        pass
    
    @abstractmethod
    async def stop_scanning(self) -> None:
        """Stop BLE scanning"""
        pass
    
    @abstractmethod
    async def get_devices(self) -> List[BLEDevice]:
        """Get list of discovered devices"""
        pass
    
    @abstractmethod
    async def connect(self, address: str, security_requirements: Optional[SecurityRequirements] = None) -> bool:
        """Connect to a specific device with optional security requirements"""
        pass
    
    @abstractmethod
    async def disconnect(self, address: str) -> None:
        """Disconnect from a device"""
        pass
    
    @abstractmethod
    async def packet_stream(self) -> AsyncIterator[BLEPacket]:
        """Stream BLE packets as they arrive"""
        pass
    
    @abstractmethod
    async def discover_services(self, address: str) -> List[BLEService]:
        """Discover GATT services for a connected device"""
        pass
    
    @abstractmethod
    async def discover_characteristics(self, address: str, service_uuid: str) -> List[BLECharacteristic]:
        """Discover characteristics for a specific service"""
        pass
    
    @abstractmethod
    async def discover_descriptors(self, address: str, char_uuid: str) -> List[BLEDescriptor]:
        """Discover descriptors for a specific characteristic"""
        pass
    
    @abstractmethod
    async def read_characteristic(self, address: str, char_uuid: str) -> Optional[bytes]:
        """Read value from a characteristic"""
        pass
    
    @abstractmethod
    async def write_characteristic(self, address: str, char_uuid: str, data: bytes) -> bool:
        """Write value to a characteristic"""
        pass
    
    def register_callback(self, callback: Callable[[BLEPacket], None]) -> None:
        """Register a callback for packet events"""
        self._callbacks.append(callback)
    
    def _emit_packet(self, packet: BLEPacket) -> None:
        """Emit packet to all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(packet)
            except Exception as e:
                print(f"Callback error: {e}")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    async def pair_device(self, address: str) -> bool:
        """Pair with a device using the security manager"""
        return await self.security_manager.request_pairing(address)
    
    def is_bonded(self, address: str) -> bool:
        """Check if device is bonded"""
        return self.security_manager.is_bonded(address)
    
    async def handle_security_error(self, address: str, error: Exception) -> bool:
        """Handle security-related errors during operations"""
        # Check if this is a security error that can be resolved by pairing
        error_msg = str(error).lower()
        if any(keyword in error_msg for keyword in ['auth', 'encrypt', 'pair', 'bond', 'security']):
            # Try to pair and retry
            if await self.pair_device(address):
                return True
        return False