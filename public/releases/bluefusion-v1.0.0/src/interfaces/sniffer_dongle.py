import asyncio
import serial
import serial.tools.list_ports
from typing import List, Dict, Any, AsyncIterator, Optional
from datetime import datetime
import struct

from .base import BLEInterface, BLEDevice, BLEPacket, DeviceType, BLEService, BLECharacteristic, BLEDescriptor
from .channel_hopper import ChannelHopper, SmartChannelHopper
from ..utils.serial_utils import find_ble_sniffer_port, is_port_available


class SnifferDongle(BLEInterface):
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, security_manager=None):
        super().__init__(DeviceType.SNIFFER_DONGLE, security_manager)
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self._initialized = False  # Track if we successfully initialized at least once
        self._last_error: Optional[str] = None  # Track last error for debugging
        self.discovered_devices: Dict[str, BLEDevice] = {}
        self._packet_queue: asyncio.Queue[BLEPacket] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        self.channel_hopper: Optional[SmartChannelHopper] = None
        self.current_channel = 37  # Default to advertising channel
    
    async def initialize(self) -> None:
        """Initialize the sniffer dongle"""
        if self.port is None:
            self.port = await self._auto_detect_port()
        
        if self.port:
            try:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=0.1
                )
                # Verify the connection is actually working
                if self.serial_conn.is_open:
                    await self._send_command(b"INIT")
                    print(f"Sniffer serial connection established on {self.port}")
                    self._initialized = True
                    self._last_error = None
                else:
                    error_msg = f"Failed to open serial connection on {self.port}"
                    print(error_msg)
                    self._last_error = error_msg
                    self.serial_conn = None
            except serial.SerialException as e:
                error_msg = f"Failed to initialize serial connection on {self.port}: {e}"
                print(error_msg)
                self._last_error = error_msg
                self.serial_conn = None
            except Exception as e:
                error_msg = f"Unexpected error initializing sniffer on {self.port}: {e}"
                print(error_msg)
                self._last_error = error_msg
                self.serial_conn = None
    
    async def _auto_detect_port(self) -> Optional[str]:
        """Auto-detect the sniffer dongle port"""
        return find_ble_sniffer_port()
    
    def check_connection(self) -> bool:
        """Check if the serial connection is still valid and port is available"""
        # If we were never initialized successfully, we're not connected
        if not self._initialized or not self.port:
            return False
        
        # If we have an open serial connection, assume it's working
        # Don't try to re-open the port as that will fail
        if self.serial_conn and hasattr(self.serial_conn, 'is_open'):
            try:
                return self.serial_conn.is_open
            except:
                return False
        
        # No serial connection object
        return False
    
    def is_connected(self) -> bool:
        """Check if we have a valid connection to the sniffer dongle"""
        # This is the method that should be used for status checks
        # It checks if we were initialized and have a connection object
        return self._initialized and self.serial_conn is not None
    
    async def _send_command(self, command: bytes) -> None:
        """Send command to the sniffer"""
        if self.serial_conn:
            try:
                self.serial_conn.write(command + b'\n')
                self.serial_conn.flush()  # Ensure command is sent
            except serial.SerialException as e:
                # Don't set serial_conn to None - just log the error
                self._last_error = f"Failed to send command {command}: {e}"
                print(self._last_error)
    
    def _read_packet(self) -> Optional[bytes]:
        """Read a packet from the serial connection"""
        if not self.check_connection():
            return None
        
        try:
            # Example packet format (adapt to your sniffer's protocol)
            # [SYNC_BYTE][LENGTH][PACKET_TYPE][DATA...][CRC]
            
            sync = self.serial_conn.read(1)
            if not sync or sync != b'\xAA':  # Example sync byte
                return None
            
            length_bytes = self.serial_conn.read(2)
            if len(length_bytes) < 2:
                return None
            
            length = struct.unpack('>H', length_bytes)[0]
            packet_data = self.serial_conn.read(length)
            
            if len(packet_data) < length:
                return None
            
            return packet_data
        except serial.SerialException as e:
            # Don't set serial_conn to None on read errors - the connection might recover
            # Just log the error and return None for this packet
            self._last_error = f"Serial read error: {e}"
            return None
        except Exception as e:
            # Log error but don't disconnect
            self._last_error = f"Unexpected error reading packet: {e}"
            return None
    
    async def _reader_loop(self):
        """Main reader loop for the sniffer"""
        while self._running:
            try:
                packet_data = await asyncio.get_event_loop().run_in_executor(
                    None, self._read_packet
                )
                
                if packet_data:
                    packet = self._parse_packet(packet_data)
                    if packet:
                        self._emit_packet(packet)
                        await self._packet_queue.put(packet)
                
                await asyncio.sleep(0.001)  # Small delay
            except Exception as e:
                print(f"Reader error: {e}")
    
    def _parse_packet(self, data: bytes) -> Optional[BLEPacket]:
        """Parse raw packet data into BLEPacket"""
        # Example parsing (adapt to your sniffer format)
        try:
            # Extract basic info
            packet_type = data[0]
            timestamp_ms = struct.unpack('>I', data[1:5])[0]
            channel = data[5]
            rssi = struct.unpack('b', data[6:7])[0]
            address = data[7:13].hex(':')
            payload = data[13:]
            
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=self.device_type,
                address=address,
                rssi=rssi,
                data=payload,
                packet_type=self._get_packet_type_name(packet_type),
                metadata={
                    "channel": channel,
                    "timestamp_ms": timestamp_ms,
                    "raw_type": packet_type
                }
            )
            
            # Update channel activity for adaptive hopping
            if self.channel_hopper:
                self.channel_hopper.update_channel_activity(channel)
            
            # Update current channel
            self.current_channel = channel
            
            # Update device list
            if address not in self.discovered_devices:
                self.discovered_devices[address] = BLEDevice(
                    address=address,
                    rssi=rssi,
                    raw_data=data
                )
            
            return packet
        except Exception as e:
            print(f"Packet parse error: {e}")
            return None
    
    def _get_packet_type_name(self, packet_type: int) -> str:
        """Convert packet type number to name"""
        types = {
            0x00: "advertisement",
            0x01: "scan_request",
            0x02: "scan_response",
            0x03: "connection_request",
            0x04: "connection_response",
            0x10: "data_packet",
        }
        return types.get(packet_type, f"unknown_{packet_type}")
    
    async def start_scanning(self, passive: bool = False) -> None:
        """Start BLE scanning"""
        if self.serial_conn is None:
            await self.initialize()
        
        # Check if initialization was successful
        if self.serial_conn is None:
            raise Exception("Failed to initialize sniffer connection")
        
        self._running = True
        
        # Configure sniffer for passive/active scanning
        if passive:
            await self._send_command(b"MODE PASSIVE")
        else:
            await self._send_command(b"MODE ACTIVE")
        
        await self._send_command(b"START")
        
        # Start reader task
        self._reader_task = asyncio.create_task(self._reader_loop())
        
        # Initialize and start channel hopping
        self.channel_hopper = SmartChannelHopper(self)
        await self.channel_hopper.start_adaptive_hopping(base_interval=0.1)
    
    async def stop_scanning(self) -> None:
        """Stop BLE scanning"""
        self._running = False
        
        # Stop channel hopping
        if self.channel_hopper:
            await self.channel_hopper.stop_hopping()
        
        if self.serial_conn:
            await self._send_command(b"STOP")
        
        if self._reader_task:
            await self._reader_task
            self._reader_task = None
    
    async def get_devices(self) -> List[BLEDevice]:
        """Get list of discovered devices"""
        return list(self.discovered_devices.values())
    
    async def connect(self, address: str) -> bool:
        """Connect to a specific device (if supported by sniffer)"""
        # Most sniffers are passive only
        print("Sniffer dongles typically don't support active connections")
        return False
    
    async def disconnect(self, address: str) -> None:
        """Disconnect from a device"""
        pass
    
    async def packet_stream(self) -> AsyncIterator[BLEPacket]:
        """Stream BLE packets as they arrive"""
        while self._running:
            packet = await self._packet_queue.get()
            yield packet
    
    async def set_channel(self, channel: int) -> None:
        """Set the BLE channel to monitor (37, 38, 39 for advertising)"""
        if 0 <= channel <= 39:
            await self._send_command(f"CHANNEL {channel}".encode())
    
    async def set_follow_mode(self, address: str) -> None:
        """Follow a specific device's connection"""
        await self._send_command(f"FOLLOW {address}".encode())
    
    async def discover_services(self, address: str) -> List[BLEService]:
        """Discover GATT services for a connected device"""
        # Sniffer dongles cannot directly discover services since they only monitor traffic
        # This method would need to be implemented differently or not supported
        print(f"Service discovery not supported on sniffer dongle for {address}")
        return []
    
    async def discover_characteristics(self, address: str, service_uuid: str) -> List[BLECharacteristic]:
        """Discover characteristics for a specific service"""
        # Sniffer dongles cannot directly discover characteristics
        print(f"Characteristic discovery not supported on sniffer dongle for {address}")
        return []
    
    async def discover_descriptors(self, address: str, char_uuid: str) -> List[BLEDescriptor]:
        """Discover descriptors for a specific characteristic"""
        # Sniffer dongles cannot directly discover descriptors
        print(f"Descriptor discovery not supported on sniffer dongle for {address}")
        return []