import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
from datetime import datetime
import bleak
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice as BleakDevice

from .base import BLEInterface, BLEDevice, BLEPacket, DeviceType, SecurityRequirements, SecurityManager, BLEService, BLECharacteristic, BLEDescriptor
from .ble_errors import BLESecurityException, BLEPairingRequired, BLEAuthenticationRequired


class MacBookBLE(BLEInterface):
    def __init__(self, security_manager: Optional[SecurityManager] = None):
        super().__init__(DeviceType.MACBOOK_BLE, security_manager)
        self.scanner: Optional[BleakScanner] = None
        self.discovered_devices: Dict[str, BLEDevice] = {}
        self.connected_clients: Dict[str, BleakClient] = {}
        self._packet_queue: asyncio.Queue[BLEPacket] = asyncio.Queue()
    
    async def initialize(self) -> None:
        """Initialize the MacBook BLE interface"""
        self.scanner = BleakScanner(
            detection_callback=self._detection_callback,
            service_uuids=None
        )
    
    def _detection_callback(self, device: BleakDevice, advertisement_data: Dict[str, Any]):
        """Callback for device detection"""
        ble_device = BLEDevice(
            address=device.address,
            name=device.name,
            rssi=advertisement_data.rssi,
            manufacturer_data=dict(advertisement_data.manufacturer_data),
            service_data=dict(advertisement_data.service_data),
            services=list(advertisement_data.service_uuids),
            raw_data=None
        )
        
        self.discovered_devices[device.address] = ble_device
        
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=self.device_type,
            address=device.address,
            rssi=advertisement_data.rssi,
            data=b"",  # Advertisement data
            packet_type="advertisement",
            metadata={
                "name": device.name,
                "services": list(advertisement_data.service_uuids),
                "manufacturer_data": {k: v.hex() for k, v in advertisement_data.manufacturer_data.items()},
                "service_data": {k: v.hex() for k, v in advertisement_data.service_data.items()},
            }
        )
        
        self._emit_packet(packet)
        asyncio.create_task(self._packet_queue.put(packet))
    
    async def start_scanning(self, passive: bool = False) -> None:
        """Start BLE scanning"""
        if self.scanner is None:
            await self.initialize()
        
        self._running = True
        await self.scanner.start()
    
    async def stop_scanning(self) -> None:
        """Stop BLE scanning"""
        if self.scanner:
            await self.scanner.stop()
        self._running = False
    
    async def get_devices(self) -> List[BLEDevice]:
        """Get list of discovered devices"""
        return list(self.discovered_devices.values())
    
    async def connect(self, address: str, security_requirements: Optional[SecurityRequirements] = None) -> bool:
        """Connect to a specific device with optional security requirements"""
        try:
            # Check if we need to pair first
            if security_requirements and not self.security_manager.check_security_requirements(address, security_requirements):
                # Need to pair first
                if not await self.pair_device(address):
                    raise BLEPairingRequired(None, address)
            
            client = BleakClient(address)
            await client.connect()
            self.connected_clients[address] = client
            
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=0,
                data=b"",
                packet_type="connection",
                metadata={"status": "connected", "bonded": self.is_bonded(address)}
            )
            self._emit_packet(packet)
            
            return True
        except Exception as e:
            # Try to handle security errors
            if await self.handle_security_error(address, e):
                # Retry connection after successful pairing
                return await self.connect(address, security_requirements)
            
            print(f"Connection failed: {e}")
            return False
    
    async def disconnect(self, address: str) -> None:
        """Disconnect from a device"""
        if address in self.connected_clients:
            client = self.connected_clients[address]
            await client.disconnect()
            del self.connected_clients[address]
            
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=0,
                data=b"",
                packet_type="disconnection",
                metadata={"status": "disconnected"}
            )
            self._emit_packet(packet)
    
    async def packet_stream(self) -> AsyncIterator[BLEPacket]:
        """Stream BLE packets as they arrive"""
        while self._running:
            packet = await self._packet_queue.get()
            yield packet
    
    async def read_characteristic(self, address: str, char_uuid: str) -> Optional[bytes]:
        """Read a characteristic from a connected device"""
        if address in self.connected_clients:
            client = self.connected_clients[address]
            try:
                data = await client.read_gatt_char(char_uuid)
                
                packet = BLEPacket(
                    timestamp=datetime.now(),
                    source=self.device_type,
                    address=address,
                    rssi=0,
                    data=data,
                    packet_type="gatt_read",
                    metadata={"characteristic": char_uuid}
                )
                self._emit_packet(packet)
                
                return data
            except Exception as e:
                # Handle security errors specifically
                if await self.handle_security_error(address, e):
                    # Retry read after successful pairing
                    try:
                        data = await client.read_gatt_char(char_uuid)
                        return data
                    except Exception as retry_error:
                        print(f"Read failed after pairing: {retry_error}")
                
                print(f"Read failed: {e}")
                return None
        return None
    
    async def write_characteristic(self, address: str, char_uuid: str, data: bytes, with_response: bool = True) -> bool:
        """Write to a characteristic on a connected device"""
        if address in self.connected_clients:
            client = self.connected_clients[address]
            try:
                await client.write_gatt_char(char_uuid, data, with_response)
                
                packet = BLEPacket(
                    timestamp=datetime.now(),
                    source=self.device_type,
                    address=address,
                    rssi=0,
                    data=data,
                    packet_type="gatt_write",
                    metadata={"characteristic": char_uuid, "with_response": with_response}
                )
                self._emit_packet(packet)
                
                return True
            except Exception as e:
                # Handle security errors specifically
                if await self.handle_security_error(address, e):
                    # Retry write after successful pairing
                    try:
                        await client.write_gatt_char(char_uuid, data, with_response)
                        return True
                    except Exception as retry_error:
                        print(f"Write failed after pairing: {retry_error}")
                
                print(f"Write failed: {e}")
                return False
        return False
    
    async def subscribe_notifications(self, address: str, char_uuid: str, callback) -> bool:
        """Subscribe to notifications from a characteristic"""
        if address in self.connected_clients:
            client = self.connected_clients[address]
            try:
                await client.start_notify(char_uuid, callback)
                return True
            except Exception as e:
                # Handle security errors specifically
                if await self.handle_security_error(address, e):
                    # Retry subscription after successful pairing
                    try:
                        await client.start_notify(char_uuid, callback)
                        return True
                    except Exception as retry_error:
                        print(f"Subscribe failed after pairing: {retry_error}")
                
                print(f"Subscribe failed: {e}")
                return False
        return False
    
    async def discover_services(self, address: str) -> List[BLEService]:
        """Discover GATT services for a connected device"""
        if address not in self.connected_clients:
            print(f"Device {address} not connected")
            return []
        
        client = self.connected_clients[address]
        try:
            services = await client.get_services()
            
            ble_services = []
            for service in services:
                ble_service = BLEService(
                    uuid=str(service.uuid),
                    handle=service.handle if hasattr(service, 'handle') else None,
                    primary=True  # Bleak doesn't distinguish primary/secondary
                )
                ble_services.append(ble_service)
            
            # Store discovered services in the device
            if address in self.discovered_devices:
                self.discovered_devices[address].discovered_services = ble_services
            
            # Emit packet for service discovery
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=0,
                data=b"",
                packet_type="service_discovery",
                metadata={
                    "services_count": len(ble_services),
                    "services": [s.uuid for s in ble_services]
                }
            )
            self._emit_packet(packet)
            
            return ble_services
        except Exception as e:
            if await self.handle_security_error(address, e):
                return await self.discover_services(address)
            print(f"Service discovery failed: {e}")
            return []
    
    async def discover_characteristics(self, address: str, service_uuid: str) -> List[BLECharacteristic]:
        """Discover characteristics for a specific service"""
        if address not in self.connected_clients:
            print(f"Device {address} not connected")
            return []
        
        client = self.connected_clients[address]
        try:
            services = await client.get_services()
            target_service = None
            
            for service in services:
                if str(service.uuid) == service_uuid:
                    target_service = service
                    break
            
            if not target_service:
                print(f"Service {service_uuid} not found")
                return []
            
            characteristics = []
            for char in target_service.characteristics:
                properties = []
                if char.properties:
                    if char.properties & 0x02:  # Read
                        properties.append("read")
                    if char.properties & 0x04:  # Write without response
                        properties.append("write-without-response")
                    if char.properties & 0x08:  # Write
                        properties.append("write")
                    if char.properties & 0x10:  # Notify
                        properties.append("notify")
                    if char.properties & 0x20:  # Indicate
                        properties.append("indicate")
                
                ble_char = BLECharacteristic(
                    uuid=str(char.uuid),
                    handle=char.handle if hasattr(char, 'handle') else None,
                    properties=properties
                )
                characteristics.append(ble_char)
            
            # Emit packet for characteristic discovery
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=0,
                data=b"",
                packet_type="characteristic_discovery",
                metadata={
                    "service_uuid": service_uuid,
                    "characteristics_count": len(characteristics),
                    "characteristics": [c.uuid for c in characteristics]
                }
            )
            self._emit_packet(packet)
            
            return characteristics
        except Exception as e:
            if await self.handle_security_error(address, e):
                return await self.discover_characteristics(address, service_uuid)
            print(f"Characteristic discovery failed: {e}")
            return []
    
    async def discover_descriptors(self, address: str, char_uuid: str) -> List[BLEDescriptor]:
        """Discover descriptors for a specific characteristic"""
        if address not in self.connected_clients:
            print(f"Device {address} not connected")
            return []
        
        client = self.connected_clients[address]
        try:
            services = await client.get_services()
            target_char = None
            
            # Find the characteristic
            for service in services:
                for char in service.characteristics:
                    if str(char.uuid) == char_uuid:
                        target_char = char
                        break
                if target_char:
                    break
            
            if not target_char:
                print(f"Characteristic {char_uuid} not found")
                return []
            
            descriptors = []
            for desc in target_char.descriptors:
                ble_desc = BLEDescriptor(
                    uuid=str(desc.uuid),
                    handle=desc.handle if hasattr(desc, 'handle') else None
                )
                descriptors.append(ble_desc)
            
            # Emit packet for descriptor discovery
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=0,
                data=b"",
                packet_type="descriptor_discovery",
                metadata={
                    "characteristic_uuid": char_uuid,
                    "descriptors_count": len(descriptors),
                    "descriptors": [d.uuid for d in descriptors]
                }
            )
            self._emit_packet(packet)
            
            return descriptors
        except Exception as e:
            if await self.handle_security_error(address, e):
                return await self.discover_descriptors(address, char_uuid)
            print(f"Descriptor discovery failed: {e}")
            return []