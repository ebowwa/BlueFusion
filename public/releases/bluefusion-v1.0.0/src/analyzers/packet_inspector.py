"""
Packet Inspector - Core component for deep BLE packet analysis
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pydantic import BaseModel
from ..interfaces.base import BLEPacket
import struct


class InspectionResult(BaseModel):
    """Result of packet inspection"""
    packet_id: str
    timestamp: datetime
    protocol: Optional[str] = None
    fields: Dict[str, Any] = {}
    raw_hex: str = ""
    parsed_data: Dict[str, Any] = {}
    warnings: List[str] = []
    security_flags: Dict[str, bool] = {}
    
    class Config:
        arbitrary_types_allowed = True


class PacketInspector:
    """Advanced packet analysis and debugging tool"""
    
    def __init__(self):
        self.parsers = {}
        self.packet_history = []
        self.max_history = 1000
    
    def inspect_packet(self, packet: BLEPacket) -> InspectionResult:
        """
        Perform deep inspection of a BLE packet
        
        Args:
            packet: BLEPacket to inspect
            
        Returns:
            InspectionResult with detailed analysis
        """
        # Generate unique packet ID
        packet_id = f"{packet.address}_{packet.timestamp.timestamp()}"
        
        # Convert packet data to hex
        raw_hex = self._to_hex_dump(packet.data)
        
        # Detect protocol type
        protocol = self._detect_protocol(packet)
        
        # Parse packet fields
        fields = self._extract_basic_fields(packet)
        
        # Protocol-specific parsing
        parsed_data = {}
        if protocol and protocol in self.parsers:
            try:
                parsed_data = self.parsers[protocol].parse(packet.data)
            except Exception as e:
                parsed_data = {"error": str(e)}
        
        # Security analysis
        security_flags = self._analyze_security(packet)
        
        # Check for anomalies
        warnings = self._check_anomalies(packet, parsed_data)
        
        result = InspectionResult(
            packet_id=packet_id,
            timestamp=packet.timestamp,
            protocol=protocol,
            fields=fields,
            raw_hex=raw_hex,
            parsed_data=parsed_data,
            warnings=warnings,
            security_flags=security_flags
        )
        
        # Store in history
        self._add_to_history(result)
        
        return result
    
    def _to_hex_dump(self, data: bytes) -> str:
        """Convert bytes to formatted hex dump"""
        if not data:
            return ""
        
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f"{b:02x}" for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{i:04x}: {hex_part:<48} {ascii_part}")
        
        return '\n'.join(lines)
    
    def _detect_protocol(self, packet: BLEPacket) -> Optional[str]:
        """Detect BLE protocol type from packet"""
        # Advertisement packets have their own type
        if packet.packet_type == "advertisement":
            return "ADV"
            
        if not packet.data or len(packet.data) < 1:
            return None
        
        # Check for common BLE protocol patterns
        first_byte = packet.data[0]
        
        # L2CAP check first (it wraps other protocols)
        if len(packet.data) >= 4:
            # Check if this looks like an L2CAP packet
            # L2CAP has length in first 2 bytes and CID in next 2
            cid = struct.unpack("<H", packet.data[2:4])[0]
            if cid == 0x0004:  # ATT CID
                return "L2CAP_ATT"
            elif cid == 0x0005:  # Signaling
                # But only if the first bytes make sense as length
                length = struct.unpack("<H", packet.data[0:2])[0]
                if length > 0 and length < 100:  # Reasonable L2CAP length
                    return "L2CAP_SIG"
        
        # ATT Protocol (0x01-0x1D are valid ATT opcodes, plus some in 0x50s)
        if (0x01 <= first_byte <= 0x1E) or first_byte == 0x52 or first_byte == 0xD2:
            return "ATT"
        
        # SMP (Security Manager Protocol) on CID 0x0006
        if first_byte in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06]:
            # Could be SMP, but need more context to be sure
            # For now, treat as ATT if it matches ATT opcodes
            if first_byte == 0x01:  # Both ATT Error and SMP Pairing Request
                return "ATT"
        
        return "UNKNOWN"
    
    def _extract_basic_fields(self, packet: BLEPacket) -> Dict[str, Any]:
        """Extract basic packet fields"""
        fields = {
            "address": packet.address,
            "rssi": packet.rssi,
            "packet_type": packet.packet_type,
            "source": packet.source.value,
            "data_length": len(packet.data) if packet.data else 0,
        }
        
        # Add metadata fields
        if packet.metadata:
            fields.update(packet.metadata)
        
        return fields
    
    def _analyze_security(self, packet: BLEPacket) -> Dict[str, bool]:
        """Analyze packet for security indicators"""
        flags = {
            "encrypted": False,
            "authenticated": False,
            "contains_key": False,
            "pairing_request": False,
        }
        
        if not packet.data or len(packet.data) < 2:
            return flags
        
        # Check for encryption indicators
        # This is simplified - real analysis would be more complex
        opcode = packet.data[0] if packet.data else 0
        
        # Check for pairing request (0x01) or pairing response (0x02)
        if opcode in [0x01, 0x02]:
            flags["pairing_request"] = True
        
        # Check for encrypted data patterns
        # (In real implementation, this would be more sophisticated)
        if len(packet.data) > 16:
            # Check for high entropy (possible encryption)
            unique_bytes = len(set(packet.data))
            if unique_bytes > len(packet.data) * 0.7:
                flags["encrypted"] = True
        
        return flags
    
    def _check_anomalies(self, packet: BLEPacket, parsed_data: Dict[str, Any]) -> List[str]:
        """Check for packet anomalies or suspicious patterns"""
        warnings = []
        
        # Check packet size
        if packet.data and len(packet.data) > 251:
            warnings.append("Packet size exceeds BLE 4.2 maximum")
        
        # Check RSSI
        if packet.rssi > 0:
            warnings.append(f"Unusual RSSI value: {packet.rssi} (positive)")
        elif packet.rssi < -100:
            warnings.append(f"Very weak signal: {packet.rssi} dBm")
        
        # Check for malformed data
        if parsed_data.get("error"):
            warnings.append(f"Parse error: {parsed_data['error']}")
        
        return warnings
    
    def _add_to_history(self, result: InspectionResult):
        """Add inspection result to history"""
        self.packet_history.append(result)
        if len(self.packet_history) > self.max_history:
            self.packet_history.pop(0)
    
    def register_parser(self, protocol: str, parser):
        """Register a protocol parser"""
        self.parsers[protocol] = parser
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get inspection statistics"""
        if not self.packet_history:
            return {"total_packets": 0}
        
        protocols = {}
        security_stats = {
            "encrypted": 0,
            "authenticated": 0,
            "pairing_requests": 0,
        }
        
        for result in self.packet_history:
            # Count protocols
            if result.protocol:
                protocols[result.protocol] = protocols.get(result.protocol, 0) + 1
            
            # Count security flags
            for flag, value in result.security_flags.items():
                if value and flag in security_stats:
                    security_stats[flag] += 1
        
        return {
            "total_packets": len(self.packet_history),
            "protocols": protocols,
            "security": security_stats,
            "warnings_count": sum(len(r.warnings) for r in self.packet_history),
        }