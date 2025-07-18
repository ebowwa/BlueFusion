"""
Tests for the Hex Pattern Matcher
"""
import pytest
from src.analyzers.hex_pattern_matcher import HexPatternMatcher, Pattern, PatternMatch


class TestHexPatternMatcher:
    """Test cases for HexPatternMatcher"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.matcher = HexPatternMatcher(min_pattern_length=2, max_pattern_length=8)
    
    def test_simple_repeating_pattern(self):
        """Test detection of simple repeating patterns"""
        # Data with repeating "AABB" pattern
        data = bytes.fromhex("AABBAABBAABB")
        result = self.matcher.analyze(data)
        
        assert len(result.patterns) > 0
        assert result.most_frequent is not None
        assert result.most_frequent.hex_pattern == "aabb"
        assert result.most_frequent.count == 3
        assert result.coverage > 0.9  # Most of data is pattern
    
    def test_multiple_patterns(self):
        """Test detection of multiple different patterns"""
        # Data with "AA" and "BB" patterns
        data = bytes.fromhex("AAAABBBBAAAABBBB")
        result = self.matcher.analyze(data)
        
        patterns_hex = [p.hex_pattern for p in result.patterns]
        assert "aaaa" in patterns_hex or "aa" in patterns_hex
        assert "bbbb" in patterns_hex or "bb" in patterns_hex
    
    def test_no_patterns(self):
        """Test with random data (no patterns)"""
        # Random-looking data
        data = bytes.fromhex("0123456789ABCDEF")
        result = self.matcher.analyze(data)
        
        # Should have low pattern count and coverage
        assert len(result.patterns) < 3
        assert result.coverage < 0.5
    
    def test_empty_data(self):
        """Test with empty data"""
        data = b""
        result = self.matcher.analyze(data)
        
        assert len(result.patterns) == 0
        assert result.most_frequent is None
        assert result.coverage == 0.0
    
    def test_single_byte_pattern(self):
        """Test detection of single byte patterns"""
        # Data with repeating "FF"
        data = bytes.fromhex("FFFFFFFFFFFF")
        result = self.matcher.analyze(data)
        
        assert len(result.patterns) > 0
        assert any(p.hex_pattern == "ff" for p in result.patterns)
    
    def test_pattern_positions(self):
        """Test that pattern positions are correctly identified"""
        # Data with "CAFE" at specific positions
        data = bytes.fromhex("00CAFE00CAFE00")
        result = self.matcher.analyze(data)
        
        cafe_pattern = next((p for p in result.patterns if p.hex_pattern == "cafe"), None)
        assert cafe_pattern is not None
        assert cafe_pattern.positions == [1, 5]  # 0-indexed positions
    
    def test_overlapping_patterns(self):
        """Test handling of overlapping patterns"""
        # Data where patterns might overlap
        data = bytes.fromhex("112233112233112233")
        result = self.matcher.analyze(data)
        
        # Should find "112233" pattern
        assert any(p.hex_pattern == "112233" for p in result.patterns)
        assert any(p.count >= 3 for p in result.patterns)
    
    def test_find_sequences(self):
        """Test arithmetic sequence detection"""
        # Arithmetic sequence: 01, 02, 03, 04, 05
        data = bytes.fromhex("0102030405")
        sequences = self.matcher.find_sequences(data)
        
        assert len(sequences) > 0
        assert sequences[0]["type"] == "arithmetic"
        assert sequences[0]["difference"] == 1
        assert sequences[0]["length"] == 5
    
    def test_find_uint16_sequences(self):
        """Test detection of multi-byte sequences"""
        # uint16 sequence (little endian): 0x0100, 0x0200, 0x0300
        data = bytes.fromhex("000100020003")
        sequences = self.matcher.find_sequences(data)
        
        uint16_seq = next((s for s in sequences if s["type"] == "arithmetic_uint16"), None)
        assert uint16_seq is not None
        assert uint16_seq["difference"] == 0x0100
        assert uint16_seq["length"] == 3
    
    def test_bit_patterns(self):
        """Test bit-level pattern detection"""
        # Data with repeating bit pattern
        data = bytes.fromhex("AA55AA55")  # 10101010 01010101 pattern
        bit_patterns = self.matcher.find_bit_patterns(data)
        
        assert len(bit_patterns) > 0
        # Should find the alternating bit pattern
    
    def test_encoding_detection_ascii(self):
        """Test ASCII encoding detection"""
        # ASCII text "Hello"
        data = b"Hello"
        encodings = self.matcher.detect_encoding(data)
        
        assert "ascii" in encodings
        assert encodings["ascii"]["confidence"] == 1.0
        assert encodings["ascii"]["decoded"] == "Hello"
    
    def test_encoding_detection_bcd(self):
        """Test BCD encoding detection"""
        # BCD encoded "1234"
        data = bytes.fromhex("1234")
        encodings = self.matcher.detect_encoding(data)
        
        assert "bcd" in encodings
        assert encodings["bcd"]["decoded"] == "1234"
    
    def test_entropy_calculation(self):
        """Test entropy calculation"""
        # Low entropy (repeated data)
        low_entropy_data = bytes.fromhex("00000000")
        result_low = self.matcher.analyze(low_entropy_data)
        
        # High entropy (random-looking data)
        high_entropy_data = bytes.fromhex("1A2B3C4D")
        result_high = self.matcher.analyze(high_entropy_data)
        
        assert result_low.entropy < result_high.entropy
        assert result_low.entropy < 0.5
        assert result_high.entropy > 0.5
    
    def test_pattern_frequency(self):
        """Test pattern frequency calculation"""
        # Data where "AB" appears 3 times out of 5 possible positions
        data = bytes.fromhex("ABABAB00")
        result = self.matcher.analyze(data)
        
        ab_pattern = next((p for p in result.patterns if p.hex_pattern == "ab"), None)
        assert ab_pattern is not None
        assert ab_pattern.count == 3
        assert ab_pattern.frequency == 3 / 7  # 3 occurrences, 7 possible positions for length-2 pattern
    
    def test_different_pattern_lengths(self):
        """Test detection with different min/max pattern lengths"""
        # Adjust matcher settings
        self.matcher.min_pattern_length = 4
        self.matcher.max_pattern_length = 4
        
        # Data with 4-byte pattern
        data = bytes.fromhex("DEADBEEFDEADBEEF")
        result = self.matcher.analyze(data)
        
        assert len(result.patterns) > 0
        assert result.most_frequent.hex_pattern == "deadbeef"
        assert result.most_frequent.length == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])