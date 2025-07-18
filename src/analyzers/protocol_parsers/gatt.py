"""
GATT (Generic Attribute Profile) Protocol Parser
"""
from typing import Dict, Any, List
import struct
from .base import ProtocolParser, ParsedField


class GATTParser(ProtocolParser):
    """Parser for GATT/ATT protocol packets"""
    
    # ATT Opcodes
    ATT_OPCODES = {
        0x01: "Error Response",
        0x02: "Exchange MTU Request",
        0x03: "Exchange MTU Response",
        0x04: "Find Information Request",
        0x05: "Find Information Response",
        0x06: "Find By Type Value Request",
        0x07: "Find By Type Value Response",
        0x08: "Read By Type Request",
        0x09: "Read By Type Response",
        0x0A: "Read Request",
        0x0B: "Read Response",
        0x0C: "Read Blob Request",
        0x0D: "Read Blob Response",
        0x0E: "Read Multiple Request",
        0x0F: "Read Multiple Response",
        0x10: "Read By Group Type Request",
        0x11: "Read By Group Type Response",
        0x12: "Write Request",
        0x13: "Write Response",
        0x16: "Prepare Write Request",
        0x17: "Prepare Write Response",
        0x18: "Execute Write Request",
        0x19: "Execute Write Response",
        0x1B: "Handle Value Notification",
        0x1D: "Handle Value Indication",
        0x1E: "Handle Value Confirmation",
        0x52: "Write Command",
        0xD2: "Signed Write Command",
    }
    
    # Error codes
    ERROR_CODES = {
        0x01: "Invalid Handle",
        0x02: "Read Not Permitted",
        0x03: "Write Not Permitted",
        0x04: "Invalid PDU",
        0x05: "Insufficient Authentication",
        0x06: "Request Not Supported",
        0x07: "Invalid Offset",
        0x08: "Insufficient Authorization",
        0x09: "Prepare Queue Full",
        0x0A: "Attribute Not Found",
        0x0B: "Attribute Not Long",
        0x0C: "Insufficient Encryption Key Size",
        0x0D: "Invalid Attribute Value Length",
        0x0E: "Unlikely Error",
        0x0F: "Insufficient Encryption",
        0x10: "Unsupported Group Type",
        0x11: "Insufficient Resources",
    }
    
    def can_parse(self, data: bytes) -> bool:
        """Check if this is an ATT packet"""
        if not data or len(data) < 1:
            return False
        opcode = data[0]
        return opcode in self.ATT_OPCODES
    
    def parse(self, data: bytes) -> Dict[str, Any]:
        """Parse ATT/GATT packet"""
        if not data or len(data) < 1:
            return {"error": "Empty packet"}
        
        opcode = data[0]
        result = {
            "opcode": opcode,
            "opcode_name": self.ATT_OPCODES.get(opcode, f"Unknown (0x{opcode:02X})"),
            "length": len(data),
        }
        
        # Parse based on opcode
        if opcode == 0x01:  # Error Response
            result.update(self._parse_error_response(data))
        elif opcode == 0x02:  # Exchange MTU Request
            result.update(self._parse_mtu_request(data))
        elif opcode == 0x03:  # Exchange MTU Response
            result.update(self._parse_mtu_response(data))
        elif opcode == 0x0A:  # Read Request
            result.update(self._parse_read_request(data))
        elif opcode == 0x0B:  # Read Response
            result.update(self._parse_read_response(data))
        elif opcode == 0x12:  # Write Request
            result.update(self._parse_write_request(data))
        elif opcode == 0x1B:  # Handle Value Notification
            result.update(self._parse_handle_value_notification(data))
        else:
            # Generic parsing for unhandled opcodes
            result["payload"] = data[1:].hex() if len(data) > 1 else ""
        
        return result
    
    def parse_fields(self, data: bytes) -> List[ParsedField]:
        """Parse into structured fields"""
        fields = []
        
        if not data or len(data) < 1:
            return fields
        
        # Opcode field
        opcode = data[0]
        fields.append(ParsedField(
            name="Opcode",
            value=self.ATT_OPCODES.get(opcode, f"Unknown (0x{opcode:02X})"),
            offset=0,
            size=1,
            description=f"ATT operation code: 0x{opcode:02X}"
        ))
        
        # Parse remaining fields based on opcode
        if opcode == 0x0A and len(data) >= 3:  # Read Request
            handle = struct.unpack("<H", data[1:3])[0]
            fields.append(ParsedField(
                name="Handle",
                value=f"0x{handle:04X}",
                offset=1,
                size=2,
                description="Attribute handle to read"
            ))
        
        return fields
    
    def _parse_error_response(self, data: bytes) -> Dict[str, Any]:
        """Parse Error Response"""
        if len(data) < 5:
            return {"error": "Incomplete error response"}
        
        req_opcode = data[1]
        handle = struct.unpack("<H", data[2:4])[0]
        error_code = data[4]
        
        return {
            "request_opcode": req_opcode,
            "request_opcode_name": self.ATT_OPCODES.get(req_opcode, f"Unknown (0x{req_opcode:02X})"),
            "handle": f"0x{handle:04X}",
            "error_code": error_code,
            "error_name": self.ERROR_CODES.get(error_code, f"Unknown (0x{error_code:02X})"),
        }
    
    def _parse_mtu_request(self, data: bytes) -> Dict[str, Any]:
        """Parse MTU Request"""
        if len(data) < 3:
            return {"error": "Incomplete MTU request"}
        
        mtu = struct.unpack("<H", data[1:3])[0]
        return {"client_mtu": mtu}
    
    def _parse_mtu_response(self, data: bytes) -> Dict[str, Any]:
        """Parse MTU Response"""
        if len(data) < 3:
            return {"error": "Incomplete MTU response"}
        
        mtu = struct.unpack("<H", data[1:3])[0]
        return {"server_mtu": mtu}
    
    def _parse_read_request(self, data: bytes) -> Dict[str, Any]:
        """Parse Read Request"""
        if len(data) < 3:
            return {"error": "Incomplete read request"}
        
        handle = struct.unpack("<H", data[1:3])[0]
        return {"handle": f"0x{handle:04X}"}
    
    def _parse_read_response(self, data: bytes) -> Dict[str, Any]:
        """Parse Read Response"""
        value = data[1:] if len(data) > 1 else b""
        return {
            "value": value.hex(),
            "value_length": len(value),
            "value_ascii": self._safe_ascii(value)
        }
    
    def _parse_write_request(self, data: bytes) -> Dict[str, Any]:
        """Parse Write Request"""
        if len(data) < 3:
            return {"error": "Incomplete write request"}
        
        handle = struct.unpack("<H", data[1:3])[0]
        value = data[3:] if len(data) > 3 else b""
        
        return {
            "handle": f"0x{handle:04X}",
            "value": value.hex(),
            "value_length": len(value),
            "value_ascii": self._safe_ascii(value)
        }
    
    def _parse_handle_value_notification(self, data: bytes) -> Dict[str, Any]:
        """Parse Handle Value Notification"""
        if len(data) < 3:
            return {"error": "Incomplete notification"}
        
        handle = struct.unpack("<H", data[1:3])[0]
        value = data[3:] if len(data) > 3 else b""
        
        return {
            "handle": f"0x{handle:04X}",
            "value": value.hex(),
            "value_length": len(value),
            "value_ascii": self._safe_ascii(value)
        }
    
    def _safe_ascii(self, data: bytes) -> str:
        """Convert bytes to safe ASCII representation"""
        return ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)