"""
Packet Inspector UI Integration
"""
import gradio as gr
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import sys
import os

# Import packet inspector components
try:
    from ..analyzers import PacketInspector
    from ..analyzers.protocol_parsers import GATTParser
    from ..interfaces.base import BLEPacket, DeviceType
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.analyzers import PacketInspector
    from src.analyzers.protocol_parsers import GATTParser
    from src.interfaces.base import BLEPacket, DeviceType


class PacketInspectorUI:
    """UI handler for packet inspector functionality"""
    
    def __init__(self):
        self.inspector = PacketInspector()
        self._setup_parsers()
        self.selected_packet = None
        
    def _setup_parsers(self):
        """Initialize protocol parsers"""
        gatt_parser = GATTParser()
        self.inspector.register_parser("ATT", gatt_parser)
        self.inspector.register_parser("L2CAP_ATT", gatt_parser)
    
    def inspect_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect a packet and return formatted results
        
        Args:
            packet_data: Dictionary containing packet information
            
        Returns:
            Dictionary with inspection results
        """
        try:
            # Convert to BLEPacket format if needed
            
            # Parse timestamp
            timestamp_str = packet_data.get("timestamp", datetime.now().isoformat())
            if isinstance(timestamp_str, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except:
                    timestamp = datetime.now()
            else:
                timestamp = timestamp_str
            
            # Parse source
            source_str = packet_data.get("source", "macbook_ble")
            try:
                source = DeviceType(source_str)
            except:
                # If invalid source, default to macbook_ble
                source = DeviceType.MACBOOK_BLE
            
            # Parse data - handle both hex string and raw bytes
            data_raw = packet_data.get("data", "")
            if isinstance(data_raw, str):
                if data_raw:
                    try:
                        data = bytes.fromhex(data_raw)
                    except:
                        data = bytes()
                else:
                    data = bytes()
            else:
                data = data_raw or bytes()
            
            packet = BLEPacket(
                timestamp=timestamp,
                source=source,
                address=packet_data.get("address", ""),
                rssi=int(packet_data.get("rssi", -65)),
                data=data,
                packet_type=packet_data.get("packet_type", "data"),
                metadata=packet_data.get("metadata", {})
            )
            
            # Inspect the packet
            result = self.inspector.inspect_packet(packet)
            
            # Format for UI display
            return {
                "packet_id": result.packet_id,
                "protocol": result.protocol or "Unknown",
                "timestamp": result.timestamp.strftime("%H:%M:%S.%f")[:-3],
                "fields": result.fields,
                "parsed_data": result.parsed_data,
                "hex_dump": result.raw_hex,
                "warnings": result.warnings,
                "security_flags": result.security_flags
            }
        except Exception as e:
            # Return error information for debugging
            return {
                "packet_id": "error",
                "protocol": "ERROR",
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "fields": {"error": str(e), "packet_data": str(packet_data)},
                "parsed_data": {"error": f"Failed to inspect packet: {str(e)}"},
                "hex_dump": f"Error: {str(e)}",
                "warnings": [f"Inspection failed: {str(e)}"],
                "security_flags": {}
            }
    
    def get_inspection_summary(self, inspection_result: Dict[str, Any]) -> str:
        """Format inspection result as summary text"""
        lines = []
        
        # Check for error
        if inspection_result.get('protocol') == 'ERROR':
            lines.append("**❌ Packet Inspection Error**")
            lines.append("")
            lines.append("**Error Details:**")
            if 'error' in inspection_result['fields']:
                lines.append(f"- {inspection_result['fields']['error']}")
            if 'packet_data' in inspection_result['fields']:
                lines.append("")
                lines.append("**Packet Data:**")
                lines.append(f"```\n{inspection_result['fields']['packet_data']}\n```")
            return "\n".join(lines)
        
        # Header
        lines.append(f"**Packet Inspector Report**")
        lines.append(f"Protocol: **{inspection_result['protocol']}**")
        lines.append(f"Time: {inspection_result['timestamp']}")
        lines.append("")
        
        # Basic fields
        lines.append("**Basic Information:**")
        fields = inspection_result['fields']
        lines.append(f"- Address: {fields.get('address', 'N/A')}")
        lines.append(f"- RSSI: {fields.get('rssi', 'N/A')} dBm")
        lines.append(f"- Source: {fields.get('source', 'N/A')}")
        lines.append(f"- Data Length: {fields.get('data_length', 0)} bytes")
        lines.append("")
        
        # Parsed protocol data
        if inspection_result['parsed_data']:
            lines.append("**Protocol Analysis:**")
            for key, value in inspection_result['parsed_data'].items():
                if key != "error":
                    lines.append(f"- {key}: {value}")
            lines.append("")
        
        # Security flags
        security_flags = inspection_result['security_flags']
        if any(security_flags.values()):
            lines.append("**Security Indicators:**")
            for flag, value in security_flags.items():
                if value:
                    lines.append(f"- ⚠️ {flag.replace('_', ' ').title()}")
            lines.append("")
        
        # Warnings
        if inspection_result['warnings']:
            lines.append("**Warnings:**")
            for warning in inspection_result['warnings']:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_hex_dump_display(self, inspection_result: Dict[str, Any]) -> str:
        """Format hex dump for display"""
        return f"```\n{inspection_result['hex_dump']}\n```"
    
    def get_statistics_display(self) -> pd.DataFrame:
        """Get inspector statistics as DataFrame"""
        stats = self.inspector.get_statistics()
        
        # Protocol statistics
        protocol_data = []
        for protocol, count in stats['protocols'].items():
            protocol_data.append({
                "Protocol": protocol,
                "Packet Count": count,
                "Percentage": f"{(count / stats['total_packets'] * 100):.1f}%"
            })
        
        if not protocol_data:
            protocol_data = [{"Protocol": "No data", "Packet Count": 0, "Percentage": "0%"}]
            
        return pd.DataFrame(protocol_data)
    
    def get_security_statistics(self) -> pd.DataFrame:
        """Get security statistics as DataFrame"""
        stats = self.inspector.get_statistics()
        security_stats = stats['security']
        
        security_data = [
            {"Security Event": "Encrypted Packets", "Count": security_stats.get('encrypted', 0)},
            {"Security Event": "Authenticated", "Count": security_stats.get('authenticated', 0)},
            {"Security Event": "Pairing Requests", "Count": security_stats.get('pairing_requests', 0)},
            {"Security Event": "Total Warnings", "Count": stats.get('warnings_count', 0)},
        ]
        
        return pd.DataFrame(security_data)
    
    def format_parsed_fields(self, inspection_result: Dict[str, Any]) -> pd.DataFrame:
        """Format parsed fields as DataFrame"""
        try:
            parsed_data = inspection_result.get('parsed_data', {})
            
            if not parsed_data:
                return pd.DataFrame([{"Field": "No parsed data", "Value": ""}])
            
            field_data = []
            for key, value in parsed_data.items():
                field_data.append({
                    "Field": key.replace('_', ' ').title(),
                    "Value": str(value)
                })
            
            return pd.DataFrame(field_data)
        except Exception as e:
            return pd.DataFrame([{"Field": "Error", "Value": str(e)}])