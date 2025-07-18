"""
Tests for Packet Inspector
"""
import pytest
from datetime import datetime
from src.analyzers import PacketInspector, InspectionResult
from src.interfaces.base import BLEPacket, DeviceType


class TestPacketInspector:
    """Test packet inspector functionality"""
    
    @pytest.fixture
    def inspector(self):
        """Create a packet inspector instance"""
        return PacketInspector()
    
    @pytest.fixture
    def sample_packet(self):
        """Create a sample BLE packet"""
        return BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x08, 0x00, 0x01, 0x02, 0x03, 0x04]),
            packet_type="data",
            metadata={"channel": 37}
        )
    
    def test_inspector_creation(self, inspector):
        """Test inspector initialization"""
        assert inspector is not None
        assert inspector.parsers == {}
        assert inspector.packet_history == []
        assert inspector.max_history == 1000
    
    def test_basic_inspection(self, inspector, sample_packet):
        """Test basic packet inspection"""
        result = inspector.inspect_packet(sample_packet)
        
        assert isinstance(result, InspectionResult)
        assert result.timestamp == sample_packet.timestamp
        assert result.fields["address"] == "AA:BB:CC:DD:EE:FF"
        assert result.fields["rssi"] == -65
        assert result.fields["data_length"] == 6
        assert result.raw_hex is not None
    
    def test_hex_dump(self, inspector):
        """Test hex dump generation"""
        data = bytes(range(32))
        hex_dump = inspector._to_hex_dump(data)
        
        assert "0000:" in hex_dump
        assert "0010:" in hex_dump
        assert "00 01 02 03" in hex_dump
        assert len(hex_dump.split('\n')) == 2
    
    def test_protocol_detection(self, inspector):
        """Test protocol detection"""
        # ATT packet
        att_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x08, 0x00, 0x01, 0x02]),  # ATT Read Request
            packet_type="data"
        )
        assert inspector._detect_protocol(att_packet) == "ATT"
        
        # L2CAP packet
        l2cap_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x04, 0x00, 0x04, 0x00, 0x08, 0x00]),  # L2CAP with ATT CID
            packet_type="data"
        )
        assert inspector._detect_protocol(l2cap_packet) == "L2CAP_ATT"
        
        # Advertisement packet
        adv_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x02, 0x01, 0x06]),
            packet_type="advertisement"
        )
        assert inspector._detect_protocol(adv_packet) == "ADV"
    
    def test_security_analysis(self, inspector):
        """Test security flag detection"""
        # Pairing request packet
        pairing_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x01, 0x00, 0x00, 0x00]),
            packet_type="data"
        )
        flags = inspector._analyze_security(pairing_packet)
        assert flags["pairing_request"] is True
        
        # High entropy data (possible encryption)
        random_data = bytes(range(256))[:32]
        encrypted_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=random_data,
            packet_type="data"
        )
        flags = inspector._analyze_security(encrypted_packet)
        assert flags["encrypted"] is True
    
    def test_anomaly_detection(self, inspector):
        """Test anomaly detection"""
        # Oversized packet
        large_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes(252),
            packet_type="data"
        )
        warnings = inspector._check_anomalies(large_packet, {})
        assert any("exceeds BLE 4.2 maximum" in w for w in warnings)
        
        # Unusual RSSI
        strong_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=5,
            data=bytes([0x01, 0x02]),
            packet_type="data"
        )
        warnings = inspector._check_anomalies(strong_packet, {})
        assert any("Unusual RSSI" in w for w in warnings)
    
    def test_packet_history(self, inspector):
        """Test packet history management"""
        # Add multiple packets
        for i in range(5):
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=DeviceType.MACBOOK_BLE,
                address=f"AA:BB:CC:DD:EE:{i:02X}",
                rssi=-65,
                data=bytes([i]),
                packet_type="data"
            )
            inspector.inspect_packet(packet)
        
        assert len(inspector.packet_history) == 5
        
        # Test statistics
        stats = inspector.get_statistics()
        assert stats["total_packets"] == 5
        assert "protocols" in stats
        assert "security" in stats
    
    def test_empty_packet_handling(self, inspector):
        """Test handling of empty packets"""
        empty_packet = BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes(),
            packet_type="data"
        )
        
        result = inspector.inspect_packet(empty_packet)
        assert result is not None
        assert result.fields["data_length"] == 0
        assert result.protocol is None