#!/usr/bin/env python3
"""
Packet Inspector Demo - Shows how to use the packet inspector with BlueFusion
"""
import asyncio
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.analyzers import PacketInspector
from src.analyzers.protocol_parsers import GATTParser
from src.interfaces.base import BLEPacket, DeviceType


async def demo_packet_inspector():
    """Demonstrate packet inspector functionality"""
    # Create inspector and register parsers
    inspector = PacketInspector()
    gatt_parser = GATTParser()
    
    # Register GATT parser for ATT protocols
    inspector.register_parser("ATT", gatt_parser)
    inspector.register_parser("L2CAP_ATT", gatt_parser)
    
    print("🔍 BlueFusion Packet Inspector Demo")
    print("=" * 50)
    
    # Simulate various packet types
    packets = [
        # 1. Read Request
        BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-65,
            data=bytes([0x0A, 0x03, 0x00]),  # Read handle 0x0003
            packet_type="data",
            metadata={"channel": 37}
        ),
        
        # 2. Read Response with "Hello"
        BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.SNIFFER_DONGLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-68,
            data=bytes([0x0B]) + b"Hello",
            packet_type="data",
            metadata={"channel": 37}
        ),
        
        # 3. Heart Rate Notification
        BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="11:22:33:44:55:66",
            rssi=-72,
            data=bytes([0x1B, 0x0D, 0x00, 0x00, 0x56]),  # HR: 86 bpm
            packet_type="data",
            metadata={"service": "Heart Rate"}
        ),
        
        # 4. Error Response
        BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.SNIFFER_DONGLE,
            address="AA:BB:CC:DD:EE:FF",
            rssi=-70,
            data=bytes([0x01, 0x0A, 0x05, 0x00, 0x02]),  # Read not permitted
            packet_type="data"
        ),
        
        # 5. Advertisement
        BLEPacket(
            timestamp=datetime.now(),
            source=DeviceType.MACBOOK_BLE,
            address="99:88:77:66:55:44",
            rssi=-85,
            data=bytes([0x02, 0x01, 0x06, 0x03, 0x03, 0x0F, 0x18]),
            packet_type="advertisement"
        ),
    ]
    
    # Process each packet
    for i, packet in enumerate(packets, 1):
        print(f"\n📦 Packet {i}:")
        print("-" * 40)
        
        # Inspect the packet
        result = inspector.inspect_packet(packet)
        
        # Display results
        print(f"Protocol: {result.protocol}")
        print(f"Address: {result.fields['address']}")
        print(f"RSSI: {result.fields['rssi']} dBm")
        print(f"Source: {result.fields['source']}")
        
        # Protocol-specific data
        if result.parsed_data:
            print("\n🔬 Parsed Data:")
            for key, value in result.parsed_data.items():
                if key not in ["error"]:
                    print(f"  {key}: {value}")
        
        # Security flags
        if any(result.security_flags.values()):
            print("\n🔐 Security Flags:")
            for flag, value in result.security_flags.items():
                if value:
                    print(f"  {flag}: {value}")
        
        # Warnings
        if result.warnings:
            print("\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        # Hex dump (first line only for brevity)
        print("\n📊 Hex Dump:")
        hex_lines = result.raw_hex.split('\n')
        print(f"  {hex_lines[0]}")
        if len(hex_lines) > 1:
            print(f"  ... ({len(hex_lines)-1} more lines)")
        
        await asyncio.sleep(0.1)  # Small delay for demo effect
    
    # Show statistics
    print("\n" + "=" * 50)
    print("📈 Inspector Statistics:")
    stats = inspector.get_statistics()
    print(f"Total packets analyzed: {stats['total_packets']}")
    print(f"Protocols detected: {stats['protocols']}")
    print(f"Security events: {stats['security']}")
    print(f"Total warnings: {stats['warnings_count']}")


async def demo_real_time_inspection():
    """Demonstrate real-time packet inspection"""
    print("\n\n🚀 Real-time Inspection Demo")
    print("=" * 50)
    
    inspector = PacketInspector()
    gatt_parser = GATTParser()
    inspector.register_parser("ATT", gatt_parser)
    
    # Simulate real-time packet stream
    print("Simulating real-time BLE packet stream...")
    print("(Press Ctrl+C to stop)\n")
    
    try:
        packet_count = 0
        while True:
            # Simulate random packet
            import random
            
            packet_types = [
                # Notification
                (bytes([0x1B, 0x0D, 0x00, random.randint(50, 100)]), "Heart Rate"),
                # Read Request
                (bytes([0x0A, random.randint(1, 20), 0x00]), "Read Request"),
                # Write Command
                (bytes([0x52, 0x10, 0x00, random.randint(0, 255)]), "Write Command"),
            ]
            
            data, desc = random.choice(packet_types)
            
            packet = BLEPacket(
                timestamp=datetime.now(),
                source=random.choice([DeviceType.MACBOOK_BLE, DeviceType.SNIFFER_DONGLE]),
                address=f"{random.randint(0,255):02X}:{random.randint(0,255):02X}:CC:DD:EE:FF",
                rssi=random.randint(-90, -40),
                data=data,
                packet_type="data"
            )
            
            result = inspector.inspect_packet(packet)
            
            # Compact output for real-time display
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] {result.fields['source']:<15} | "
                  f"{result.fields['address']:<17} | "
                  f"RSSI: {result.fields['rssi']:>4} | "
                  f"{result.protocol:<10} | "
                  f"{desc:<15}")
            
            packet_count += 1
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
    except KeyboardInterrupt:
        print(f"\n\nStopped after {packet_count} packets")
        
        # Final statistics
        stats = inspector.get_statistics()
        print(f"\nFinal Statistics:")
        print(f"  Protocols: {stats['protocols']}")
        print(f"  Warnings: {stats['warnings_count']}")


async def main():
    """Run all demos"""
    await demo_packet_inspector()
    await demo_real_time_inspection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo stopped by user")