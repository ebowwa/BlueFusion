"""
Hex Pattern Matcher - Find repeating patterns in BLE characteristic data
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import hashlib


@dataclass
class Pattern:
    """Represents a detected pattern in hex data"""
    pattern: bytes
    hex_pattern: str
    positions: List[int]
    length: int
    count: int
    frequency: float
    
    def __repr__(self):
        return f"Pattern({self.hex_pattern}, count={self.count}, len={self.length})"


@dataclass
class PatternMatch:
    """Result of pattern matching analysis"""
    data: bytes
    hex_data: str
    patterns: List[Pattern]
    most_frequent: Optional[Pattern]
    coverage: float  # Percentage of data covered by patterns
    entropy: float  # Data randomness measure
    
    
class HexPatternMatcher:
    """Find and analyze repeating patterns in hex data"""
    
    def __init__(self, min_pattern_length: int = 2, max_pattern_length: int = 32):
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length
        
    def analyze(self, data: bytes) -> PatternMatch:
        """
        Analyze hex data for patterns
        
        Args:
            data: Raw bytes to analyze
            
        Returns:
            PatternMatch with detected patterns
        """
        if not data or len(data) < self.min_pattern_length:
            return PatternMatch(
                data=data,
                hex_data=data.hex() if data else "",
                patterns=[],
                most_frequent=None,
                coverage=0.0,
                entropy=0.0
            )
        
        # Find all patterns
        patterns = self._find_all_patterns(data)
        
        # Sort by frequency and count
        sorted_patterns = sorted(patterns, key=lambda p: (p.count, p.length), reverse=True)
        
        # Calculate coverage
        coverage = self._calculate_coverage(data, sorted_patterns)
        
        # Calculate entropy
        entropy = self._calculate_entropy(data)
        
        return PatternMatch(
            data=data,
            hex_data=data.hex(),
            patterns=sorted_patterns,
            most_frequent=sorted_patterns[0] if sorted_patterns else None,
            coverage=coverage,
            entropy=entropy
        )
    
    def _find_all_patterns(self, data: bytes) -> List[Pattern]:
        """Find all repeating patterns in data"""
        patterns = {}
        data_len = len(data)
        
        # Try different pattern lengths
        for pattern_len in range(self.min_pattern_length, min(self.max_pattern_length + 1, data_len // 2 + 1)):
            # Slide window across data
            for start in range(data_len - pattern_len + 1):
                pattern_bytes = data[start:start + pattern_len]
                pattern_key = pattern_bytes.hex()
                
                if pattern_key not in patterns:
                    # Find all occurrences of this pattern
                    positions = self._find_pattern_positions(data, pattern_bytes)
                    
                    if len(positions) >= 2:  # Only keep patterns that repeat
                        patterns[pattern_key] = Pattern(
                            pattern=pattern_bytes,
                            hex_pattern=pattern_key,
                            positions=positions,
                            length=pattern_len,
                            count=len(positions),
                            frequency=len(positions) / (data_len - pattern_len + 1)
                        )
        
        # Remove overlapping patterns (keep longer ones)
        filtered_patterns = self._filter_overlapping_patterns(list(patterns.values()))
        
        return filtered_patterns
    
    def _find_pattern_positions(self, data: bytes, pattern: bytes) -> List[int]:
        """Find all positions where pattern occurs in data"""
        positions = []
        start = 0
        
        while True:
            pos = data.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        return positions
    
    def _filter_overlapping_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """Remove patterns that are subpatterns of longer patterns"""
        # Sort by length (descending) and count
        sorted_patterns = sorted(patterns, key=lambda p: (p.length, p.count), reverse=True)
        
        filtered = []
        covered_positions = set()
        
        for pattern in sorted_patterns:
            # Check if this pattern adds new information
            new_positions = set()
            for pos in pattern.positions:
                pos_range = set(range(pos, pos + pattern.length))
                if not pos_range.issubset(covered_positions):
                    new_positions.update(pos_range)
            
            # Keep pattern if it covers new positions
            if new_positions:
                filtered.append(pattern)
                covered_positions.update(new_positions)
        
        return filtered
    
    def _calculate_coverage(self, data: bytes, patterns: List[Pattern]) -> float:
        """Calculate percentage of data covered by patterns"""
        if not data:
            return 0.0
            
        covered_positions = set()
        
        for pattern in patterns:
            for pos in pattern.positions:
                covered_positions.update(range(pos, pos + pattern.length))
        
        return len(covered_positions) / len(data)
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
            
        # Count byte frequencies
        byte_counts = defaultdict(int)
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate entropy
        import math
        entropy = 0.0
        data_len = len(data)
        
        for count in byte_counts.values():
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)
        
        # Normalize to 0-1 range (max entropy is 8 bits)
        return min(entropy / 8.0, 1.0)
    
    def find_sequences(self, data: bytes) -> List[Dict[str, Any]]:
        """Find arithmetic or geometric sequences in data"""
        sequences = []
        
        if len(data) < 3:
            return sequences
        
        # Check for byte-level sequences
        for i in range(len(data) - 2):
            # Arithmetic sequence check
            if data[i+1] - data[i] == data[i+2] - data[i+1]:
                diff = data[i+1] - data[i]
                length = 3
                
                # Extend sequence
                j = i + 3
                while j < len(data) and data[j] - data[j-1] == diff:
                    length += 1
                    j += 1
                
                if length >= 3:
                    sequences.append({
                        "type": "arithmetic",
                        "start_pos": i,
                        "length": length,
                        "start_value": data[i],
                        "difference": diff,
                        "values": list(data[i:i+length])
                    })
        
        # Check for repeating multi-byte values (like uint16, uint32)
        for byte_size in [2, 4]:
            if len(data) >= byte_size * 3:
                for i in range(0, len(data) - byte_size * 2, byte_size):
                    # Extract values
                    val1 = int.from_bytes(data[i:i+byte_size], 'little')
                    val2 = int.from_bytes(data[i+byte_size:i+2*byte_size], 'little')
                    val3 = int.from_bytes(data[i+2*byte_size:i+3*byte_size], 'little')
                    
                    # Check for arithmetic sequence
                    if val2 - val1 == val3 - val2:
                        diff = val2 - val1
                        length = 3
                        j = i + 3 * byte_size
                        
                        while j + byte_size <= len(data):
                            next_val = int.from_bytes(data[j:j+byte_size], 'little')
                            prev_val = int.from_bytes(data[j-byte_size:j], 'little')
                            if next_val - prev_val == diff:
                                length += 1
                                j += byte_size
                            else:
                                break
                        
                        if length >= 3:
                            sequences.append({
                                "type": f"arithmetic_uint{byte_size*8}",
                                "start_pos": i,
                                "length": length,
                                "byte_size": byte_size,
                                "start_value": val1,
                                "difference": diff,
                                "endianness": "little"
                            })
        
        return sequences
    
    def find_bit_patterns(self, data: bytes) -> List[Dict[str, Any]]:
        """Find patterns at the bit level"""
        bit_patterns = []
        
        if not data:
            return bit_patterns
        
        # Convert to bit string
        bit_string = ''.join(format(byte, '08b') for byte in data)
        
        # Find repeating bit patterns
        for pattern_len in range(8, min(len(bit_string) // 2, 64) + 1, 8):
            for start in range(len(bit_string) - pattern_len + 1):
                pattern = bit_string[start:start + pattern_len]
                
                # Count occurrences
                count = 0
                pos = 0
                positions = []
                
                while pos < len(bit_string) - pattern_len + 1:
                    if bit_string[pos:pos + pattern_len] == pattern:
                        positions.append(pos)
                        count += 1
                        pos += pattern_len  # Non-overlapping search
                    else:
                        pos += 1
                
                if count >= 2:
                    bit_patterns.append({
                        "pattern": pattern,
                        "hex_pattern": hex(int(pattern, 2))[2:],
                        "bit_length": pattern_len,
                        "count": count,
                        "positions": positions,
                        "byte_positions": [p // 8 for p in positions]
                    })
        
        # Remove duplicates and sort by count
        unique_patterns = {}
        for p in bit_patterns:
            key = p["pattern"]
            if key not in unique_patterns or p["count"] > unique_patterns[key]["count"]:
                unique_patterns[key] = p
        
        return sorted(unique_patterns.values(), key=lambda x: x["count"], reverse=True)
    
    def detect_encoding(self, data: bytes) -> Dict[str, Any]:
        """Detect possible data encoding (ASCII, UTF-8, packed BCD, etc.)"""
        encodings = {}
        
        if not data:
            return encodings
        
        # Check ASCII
        ascii_chars = 0
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                ascii_chars += 1
        
        if ascii_chars > len(data) * 0.8:
            try:
                encodings["ascii"] = {
                    "confidence": ascii_chars / len(data),
                    "decoded": data.decode('ascii', errors='replace')
                }
            except:
                pass
        
        # Check UTF-8
        try:
            decoded = data.decode('utf-8')
            encodings["utf8"] = {
                "confidence": 1.0,
                "decoded": decoded
            }
        except:
            pass
        
        # Check for packed BCD (Binary Coded Decimal)
        bcd_valid = True
        bcd_values = []
        for byte in data:
            high_nibble = byte >> 4
            low_nibble = byte & 0x0F
            if high_nibble > 9 or low_nibble > 9:
                bcd_valid = False
                break
            bcd_values.append(f"{high_nibble}{low_nibble}")
        
        if bcd_valid:
            encodings["bcd"] = {
                "confidence": 1.0,
                "decoded": ''.join(bcd_values)
            }
        
        return encodings