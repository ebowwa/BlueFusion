#!/usr/bin/env python3
"""
Hex Pattern Matcher Demo
Demonstrates the pattern detection capabilities of BlueFusion
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.analyzers.hex_pattern_matcher import HexPatternMatcher


def demo_simple_patterns():
    """Demonstrate simple pattern detection"""
    print("=== Simple Pattern Detection ===")
    
    matcher = HexPatternMatcher()
    
    # Example 1: Repeating pattern
    print("\n1. Repeating Pattern (CAFE repeated)")
    data = bytes.fromhex("CAFECAFECAFE00FFCAFE")
    result = matcher.analyze(data)
    
    print(f"Data: {data.hex()}")
    print(f"Most frequent pattern: {result.most_frequent.hex_pattern if result.most_frequent else 'None'}")
    print(f"Pattern count: {result.most_frequent.count if result.most_frequent else 0}")
    print(f"Coverage: {result.coverage:.1%}")
    print(f"Entropy: {result.entropy:.2f}")
    
    # Example 2: Multiple patterns
    print("\n2. Multiple Patterns")
    data = bytes.fromhex("DEADBEEFDEADBEEF1234123456785678")
    result = matcher.analyze(data)
    
    print(f"Data: {data.hex()}")
    print("Found patterns:")
    for i, pattern in enumerate(result.patterns[:5]):
        print(f"  {i+1}. {pattern.hex_pattern} - {pattern.count} times")


def demo_sequences():
    """Demonstrate sequence detection"""
    print("\n=== Sequence Detection ===")
    
    matcher = HexPatternMatcher()
    
    # Example: Counter data
    print("\n1. Counter Sequence")
    data = bytes.fromhex("0001020304050607")
    sequences = matcher.find_sequences(data)
    
    print(f"Data: {data.hex()}")
    print("Found sequences:")
    for seq in sequences:
        print(f"  Type: {seq['type']}")
        print(f"  Start: {seq['start_value']}")
        print(f"  Difference: {seq['difference']}")
        print(f"  Length: {seq['length']}")


def demo_encoding_detection():
    """Demonstrate encoding detection"""
    print("\n=== Encoding Detection ===")
    
    matcher = HexPatternMatcher()
    
    # Example 1: ASCII text
    print("\n1. ASCII Text")
    data = b"BlueFusion"
    encodings = matcher.detect_encoding(data)
    
    print(f"Data (hex): {data.hex()}")
    print("Detected encodings:")
    for enc_type, info in encodings.items():
        print(f"  {enc_type}: {info['decoded']} (confidence: {info['confidence']:.2f})")
    
    # Example 2: Mixed data
    print("\n2. Mixed Binary Data")
    data = bytes.fromhex("48656C6C6F000A0D")  # "Hello" + null + newline + carriage return
    encodings = matcher.detect_encoding(data)
    
    print(f"Data (hex): {data.hex()}")
    print("Detected encodings:")
    for enc_type, info in encodings.items():
        print(f"  {enc_type}: {repr(info['decoded'])} (confidence: {info['confidence']:.2f})")


def demo_real_world_examples():
    """Demonstrate with real-world BLE data examples"""
    print("\n=== Real-World BLE Data Examples ===")
    
    matcher = HexPatternMatcher()
    
    # Example 1: Heart Rate Measurement
    print("\n1. Heart Rate Measurement Characteristic")
    # Flags: 0x00, Heart Rate: 72 bpm, RR intervals
    data = bytes.fromhex("004802D002E0")
    result = matcher.analyze(data)
    
    print(f"Data: {data.hex()}")
    print(f"Analysis: {len(result.patterns)} patterns found")
    if result.patterns:
        print("Patterns:")
        for pattern in result.patterns[:3]:
            print(f"  {pattern.hex_pattern} at positions {pattern.positions}")
    
    # Example 2: Temperature Measurement  
    print("\n2. Temperature Measurement")
    # Temperature in 0.1°C units: 36.5°C = 365 = 0x016D (little endian)
    data = bytes.fromhex("6D01000000")
    result = matcher.analyze(data)
    sequences = matcher.find_sequences(data)
    
    print(f"Data: {data.hex()}")
    print(f"Patterns found: {len(result.patterns)}")
    print(f"Sequences found: {len(sequences)}")
    
    # Example 3: Device Name
    print("\n3. Device Name Characteristic")
    data = b"BlueFusion-001"
    result = matcher.analyze(data)
    encodings = matcher.detect_encoding(data)
    
    print(f"Data (hex): {data.hex()}")
    print(f"Data (ASCII): {data.decode('ascii')}")
    print(f"Entropy: {result.entropy:.2f}")
    print("Encodings:", list(encodings.keys()))


def demo_bit_patterns():
    """Demonstrate bit-level pattern detection"""
    print("\n=== Bit-Level Pattern Detection ===")
    
    matcher = HexPatternMatcher()
    
    # Example: Alternating bit pattern
    print("\n1. Alternating Bit Pattern")
    data = bytes.fromhex("AA55AA55AA55")  # 10101010 01010101 pattern
    bit_patterns = matcher.find_bit_patterns(data)
    
    print(f"Data: {data.hex()}")
    print(f"Binary: {' '.join(format(b, '08b') for b in data)}")
    print(f"Found {len(bit_patterns)} bit patterns")
    
    for i, pattern in enumerate(bit_patterns[:3]):
        print(f"\n  Pattern {i+1}:")
        print(f"    Bit pattern: {pattern['pattern']}")
        print(f"    Hex: {pattern['hex_pattern']}")
        print(f"    Count: {pattern['count']}")
        print(f"    Byte positions: {pattern['byte_positions']}")


if __name__ == "__main__":
    print("BlueFusion Hex Pattern Matcher Demo")
    print("=" * 50)
    
    demo_simple_patterns()
    demo_sequences()
    demo_encoding_detection()
    demo_real_world_examples()
    demo_bit_patterns()
    
    print("\n" + "=" * 50)
    print("Demo completed!")