"""
Tests for GATT Protocol Parser
"""
import pytest
from src.analyzers.protocol_parsers import GATTParser


class TestGATTParser:
    """Test GATT parser functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create a GATT parser instance"""
        return GATTParser()
    
    def test_parser_creation(self, parser):
        """Test parser initialization"""
        assert parser is not None
        assert parser.name == "GATTParser"
    
    def test_can_parse_valid_att(self, parser):
        """Test ATT packet detection"""
        # Valid ATT opcodes
        assert parser.can_parse(bytes([0x0A]))  # Read Request
        assert parser.can_parse(bytes([0x12]))  # Write Request
        assert parser.can_parse(bytes([0x1B]))  # Notification
        
        # Invalid opcodes
        assert not parser.can_parse(bytes([0x00]))
        assert not parser.can_parse(bytes([0xFF]))
        assert not parser.can_parse(bytes())
    
    def test_parse_read_request(self, parser):
        """Test Read Request parsing"""
        # Read Request for handle 0x0003
        data = bytes([0x0A, 0x03, 0x00])
        result = parser.parse(data)
        
        assert result["opcode"] == 0x0A
        assert result["opcode_name"] == "Read Request"
        assert result["handle"] == "0x0003"
    
    def test_parse_read_response(self, parser):
        """Test Read Response parsing"""
        # Read Response with value "Hello"
        data = bytes([0x0B]) + b"Hello"
        result = parser.parse(data)
        
        assert result["opcode"] == 0x0B
        assert result["opcode_name"] == "Read Response"
        assert result["value"] == "48656c6c6f"  # "Hello" in hex
        assert result["value_length"] == 5
        assert result["value_ascii"] == "Hello"
    
    def test_parse_write_request(self, parser):
        """Test Write Request parsing"""
        # Write Request to handle 0x0010 with value [0x01, 0x02]
        data = bytes([0x12, 0x10, 0x00, 0x01, 0x02])
        result = parser.parse(data)
        
        assert result["opcode"] == 0x12
        assert result["opcode_name"] == "Write Request"
        assert result["handle"] == "0x0010"
        assert result["value"] == "0102"
        assert result["value_length"] == 2
    
    def test_parse_error_response(self, parser):
        """Test Error Response parsing"""
        # Error Response: Read not permitted for handle 0x0005
        data = bytes([0x01, 0x0A, 0x05, 0x00, 0x02])
        result = parser.parse(data)
        
        assert result["opcode"] == 0x01
        assert result["opcode_name"] == "Error Response"
        assert result["request_opcode"] == 0x0A
        assert result["request_opcode_name"] == "Read Request"
        assert result["handle"] == "0x0005"
        assert result["error_code"] == 0x02
        assert result["error_name"] == "Read Not Permitted"
    
    def test_parse_mtu_exchange(self, parser):
        """Test MTU Exchange parsing"""
        # MTU Request with MTU=512
        req_data = bytes([0x02, 0x00, 0x02])  # 512 in little endian
        req_result = parser.parse(req_data)
        
        assert req_result["opcode"] == 0x02
        assert req_result["opcode_name"] == "Exchange MTU Request"
        assert req_result["client_mtu"] == 512
        
        # MTU Response with MTU=256
        resp_data = bytes([0x03, 0x00, 0x01])  # 256 in little endian
        resp_result = parser.parse(resp_data)
        
        assert resp_result["opcode"] == 0x03
        assert resp_result["opcode_name"] == "Exchange MTU Response"
        assert resp_result["server_mtu"] == 256
    
    def test_parse_notification(self, parser):
        """Test Handle Value Notification parsing"""
        # Notification from handle 0x0025 with value [0xAA, 0xBB]
        data = bytes([0x1B, 0x25, 0x00, 0xAA, 0xBB])
        result = parser.parse(data)
        
        assert result["opcode"] == 0x1B
        assert result["opcode_name"] == "Handle Value Notification"
        assert result["handle"] == "0x0025"
        assert result["value"] == "aabb"
        assert result["value_length"] == 2
    
    def test_parse_fields(self, parser):
        """Test structured field parsing"""
        # Read Request
        data = bytes([0x0A, 0x03, 0x00])
        fields = parser.parse_fields(data)
        
        assert len(fields) == 2
        assert fields[0].name == "Opcode"
        assert fields[0].value == "Read Request"
        assert fields[1].name == "Handle"
        assert fields[1].value == "0x0003"
    
    def test_safe_ascii_conversion(self, parser):
        """Test safe ASCII conversion"""
        # Mix of printable and non-printable
        data = b"Hello\x00\x01World"
        ascii_str = parser._safe_ascii(data)
        assert ascii_str == "Hello..World"
    
    def test_empty_packet_handling(self, parser):
        """Test handling of empty packets"""
        result = parser.parse(bytes())
        assert result["error"] == "Empty packet"
        
    def test_incomplete_packet_handling(self, parser):
        """Test handling of incomplete packets"""
        # Incomplete read request (missing handle)
        data = bytes([0x0A])
        result = parser.parse(data)
        assert "error" in result or "payload" in result