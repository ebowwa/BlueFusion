"""
Integration tests for Packet Inspector with Protocol Parsers
"""
import pytest
from datetime import datetime
from src.analyzers import PacketInspector
from src.analyzers.protocol_parsers import GATTParser
from src.interfaces.base import BLEPacket, DeviceType


class TestPacketInspectorIntegration:
    """Test packet inspector integration with parsers"""
    
    @pytest.fixture
    def inspector_with_gatt(self):
        """Create a packet inspector with GATT parser"""
        inspector = PacketInspector()
        gatt_parser = GATTParser()
        inspector.register_parser("ATT", gatt_parser)
        inspector.register_parser("L2CAP_ATT", gatt_parser)
        return inspector
    
    def test_gatt_packet_inspection(self, inspector_with_gatt):
        """Test full inspection of GATT packet"""
        # Create a Read Request packet
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x0A, 0x03, 0x00]),  # Read Request for handle 0x0003
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        # Basic inspection results
        assert result.protocol == "ATT"
        assert result.fields["address"] == "AA:BB:CC:DD:EE:FF"
        assert result.fields["rssi"] == -65
        
        # Protocol-specific parsing
        assert "opcode" in result.parsed_data
        assert result.parsed_data["opcode"] == 0x0A
        assert result.parsed_data["opcode_name"] == "Read Request"
        assert result.parsed_data["handle"] == "0x0003"
        
        # Hex dump
        assert "0000: 0a 03 00" in result.raw_hex
    
    def test_notification_packet_inspection(self, inspector_with_gatt):
        """Test inspection of notification packet"""
        # Heart rate notification
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.SNIFFER_DONGLE,
            address="11:22:33:44:55:66",
            rssi=-70,
            data=bytes([0x1B, 0x0D, 0x00, 0x00, 0x56]),  # HR: 86 bpm
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        assert result.protocol == "ATT"
        assert result.parsed_data["opcode_name"] == "Handle Value Notification"
        assert result.parsed_data["handle"] == "0x000D"
        assert result.parsed_data["value"] == "0056"
        assert len(result.warnings) == 0
    
    def test_error_packet_inspection(self, inspector_with_gatt):
        """Test inspection of error response"""
        # Error: Read not permitted
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x01, 0x0A, 0x05, 0x00, 0x02]),
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        assert result.protocol == "ATT"
        assert result.parsed_data["opcode_name"] == "Error Response"
        assert result.parsed_data["error_name"] == "Read Not Permitted"
        assert result.parsed_data["handle"] == "0x0005"
    
    def test_l2cap_wrapped_att_packet(self, inspector_with_gatt):
        """Test L2CAP wrapped ATT packet"""
        # L2CAP header (length=3, CID=0x0004) + ATT Read Request
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.SNIFFER_DONGLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x03, 0x00, 0x04, 0x00, 0x0A, 0x03, 0x00]),
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        # Should detect L2CAP_ATT protocol
        assert result.protocol == "L2CAP_ATT"
        # Parser should handle the L2CAP wrapped data
        # (In a real implementation, we'd strip L2CAP header first)
    
    def test_security_flags_with_pairing(self, inspector_with_gatt):
        """Test security analysis with pairing request"""
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x01, 0x00, 0x00, 0x00]),  # Pairing request
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        assert result.security_flags["pairing_request"] is True
        assert result.protocol == "ATT"  # 0x01 is also Error Response opcode
    
    def test_statistics_with_multiple_packets(self, inspector_with_gatt):
        """Test statistics gathering"""
        packets = [
            # Read Requests
            BLEPacket(
                timestamp=datetime.now(),
                source=DeviceType.MACBOOK_BLE,
                address="AA:BB:CC:DD:EE:FF",
                rssi=-65,
                data=bytes([0x0A, 0x03, 0x00]),
                packet_type="data"
            ),
            # Write Request
            BLEPacket(
                timestamp=datetime.now(),
                source=DeviceType.MACBOOK_BLE,
                address="AA:BB:CC:DD:EE:FF",
                rssi=-65,
                data=bytes([0x12, 0x10, 0x00, 0x01]),
                packet_type="data"
            ),
            # Advertisement
            BLEPacket(
                timestamp=datetime.now(),
                source=DeviceType.SNIFFER_DONGLE,
                address="11:22:33:44:55:66",
                rssi=-80,
                data=bytes([0x02, 0x01, 0x06]),
                packet_type="advertisement"
            ),
        ]
        
        for packet in packets:
            inspector_with_gatt.inspect_packet(packet)
        
        stats = inspector_with_gatt.get_statistics()
        
        assert stats["total_packets"] == 3
        assert stats["protocols"]["ATT"] == 2
        assert stats["protocols"]["ADV"] == 1
        assert stats["warnings_count"] == 0
    
    def test_malformed_packet_handling(self, inspector_with_gatt):
        """Test handling of malformed packets"""
        # Truncated write request (missing value)
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x12, 0x10]),  # Missing handle byte and value
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        assert result.protocol == "ATT"
        # Should have error in parsed data
        assert "error" in result.parsed_data or "payload" in result.parsed_data
    
    def test_high_entropy_encryption_detection(self, inspector_with_gatt):
        """Test encryption detection"""
        # High entropy data that looks encrypted
        import random
        random.seed(42)
        encrypted_data = bytes([random.randint(0, 255) for _ in range(32)])
        
        packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.SNIFFER_DONGLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=encrypted_data,
            packet_type="data"
        )
        
        result = inspector_with_gatt.inspect_packet(packet)
        
        # Should detect possible encryption
        assert result.security_flags["encrypted"] is True