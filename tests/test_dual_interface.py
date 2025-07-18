#!/usr/bin/env python3
"""
BlueFusion Dual Interface Test
Tests both MacBook BLE and Sniffer Dongle simultaneously
"""
import asyncio
import sys
from datetime import datetime
from collections import defaultdict
import serial.tools.list_ports

from src.interfaces.macbook_ble import MacBookBLE
from src.interfaces.sniffer_dongle import SnifferDongle

class DualInterfaceTest:
    def __init__(self):
        self.mac_ble = MacBookBLE()
        self.sniffer = SnifferDongle()
        self.mac_packets = defaultdict(int)
        self.sniffer_packets = defaultdict(int)
        
    async def detect_sniffer_port(self):
        """Detect available serial ports for sniffer"""
        print("\n=== Detecting Serial Ports ===")
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            print("❌ No serial ports detected!")
            return None
            
        print(f"Found {len(ports)} serial port(s):")
        for i, port in enumerate(ports):
            print(f"  [{i}] {port.device}")
            print(f"      Description: {port.description}")
            if port.manufacturer:
                print(f"      Manufacturer: {port.manufacturer}")
            if port.vid and port.pid:
                print(f"      VID:PID: {port.vid:04X}:{port.pid:04X}")
            print()
        
        # Try auto-detection first
        auto_port = await self.sniffer._auto_detect_port()
        if auto_port:
            print(f"✅ Auto-detected sniffer on: {auto_port}")
            return auto_port
        
        # Manual selection
        if len(ports) == 1:
            print(f"Using only available port: {ports[0].device}")
            return ports[0].device
        else:
            print("Please select port number or press Enter to skip sniffer:")
            try:
                choice = input("> ").strip()
                if choice and choice.isdigit() and 0 <= int(choice) < len(ports):
                    return ports[int(choice)].device
            except:
                pass
        return None
    
    def mac_packet_callback(self, packet):
        """Callback for MacBook BLE packets"""
        self.mac_packets[packet.packet_type] += 1
        print(f"\n[MAC] {packet.packet_type} from {packet.address}")
        print(f"      RSSI: {packet.rssi} dBm")
        if packet.metadata.get('name'):
            print(f"      Name: {packet.metadata['name']}")
    
    def sniffer_packet_callback(self, packet):
        """Callback for Sniffer packets"""
        self.sniffer_packets[packet.packet_type] += 1
        print(f"\n[SNIFF] {packet.packet_type} from {packet.address}")
        print(f"        RSSI: {packet.rssi} dBm")
        print(f"        Channel: {packet.metadata.get('channel', 'N/A')}")
    
    async def test_mac_ble(self):
        """Test MacBook BLE interface"""
        print("\n=== Testing MacBook BLE Interface ===")
        
        try:
            print("Initializing MacBook BLE...")
            await self.mac_ble.initialize()
            self.mac_ble.register_callback(self.mac_packet_callback)
            
            print("✅ MacBook BLE initialized successfully")
            
            print("\nStarting 5-second scan...")
            await self.mac_ble.start_scanning()
            await asyncio.sleep(5)
            await self.mac_ble.stop_scanning()
            
            devices = await self.mac_ble.get_devices()
            print(f"\n✅ MacBook BLE found {len(devices)} devices")
            
            return True
            
        except Exception as e:
            print(f"❌ MacBook BLE error: {e}")
            return False
    
    async def test_sniffer(self, port):
        """Test Sniffer Dongle interface"""
        print("\n=== Testing Sniffer Dongle Interface ===")
        
        if not port:
            print("⚠️  No sniffer port specified, skipping sniffer test")
            return False
        
        try:
            self.sniffer.port = port
            print(f"Initializing sniffer on port {port}...")
            await self.sniffer.initialize()
            self.sniffer.register_callback(self.sniffer_packet_callback)
            
            print("✅ Sniffer initialized successfully")
            
            print("\nSetting advertising channels...")
            await self.sniffer.set_channel(37)  # BLE advertising channel
            
            print("Starting 5-second passive scan...")
            await self.sniffer.start_scanning(passive=True)
            await asyncio.sleep(5)
            await self.sniffer.stop_scanning()
            
            devices = await self.sniffer.get_devices()
            print(f"\n✅ Sniffer found {len(devices)} devices")
            
            return True
            
        except Exception as e:
            print(f"❌ Sniffer error: {e}")
            return False
    
    async def test_dual_operation(self):
        """Test both interfaces running simultaneously"""
        print("\n=== Testing Dual Interface Operation ===")
        print("Running both interfaces for 10 seconds...")
        
        # Reset counters
        self.mac_packets.clear()
        self.sniffer_packets.clear()
        
        # Start both interfaces
        tasks = []
        
        try:
            # Start MacBook BLE
            await self.mac_ble.start_scanning()
            
            # Start Sniffer if available
            if self.sniffer.serial_conn:
                await self.sniffer.start_scanning(passive=True)
            
            # Run for 10 seconds
            await asyncio.sleep(10)
            
            # Stop both
            await self.mac_ble.stop_scanning()
            if self.sniffer.serial_conn:
                await self.sniffer.stop_scanning()
            
            # Print statistics
            print("\n=== Dual Operation Statistics ===")
            print(f"\nMacBook BLE Packets:")
            for ptype, count in self.mac_packets.items():
                print(f"  {ptype}: {count}")
            
            if self.sniffer.serial_conn:
                print(f"\nSniffer Packets:")
                for ptype, count in self.sniffer_packets.items():
                    print(f"  {ptype}: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Dual operation error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("=== BlueFusion Dual Interface Test Suite ===")
        print(f"Starting at {datetime.now()}\n")
        
        # Check Bluetooth status
        print("⚠️  Make sure:")
        print("   1. Bluetooth is enabled on your Mac")
        print("   2. BLE sniffer dongle is connected (if available)")
        print("\nPress Enter to continue...")
        input()
        
        # Detect sniffer port
        sniffer_port = await self.detect_sniffer_port()
        
        # Test MacBook BLE
        mac_ok = await self.test_mac_ble()
        
        # Test Sniffer
        sniffer_ok = await self.test_sniffer(sniffer_port)
        
        # Test dual operation if at least MacBook BLE works
        if mac_ok:
            await self.test_dual_operation()
        
        # Summary
        print("\n=== Test Summary ===")
        print(f"MacBook BLE: {'✅ PASS' if mac_ok else '❌ FAIL'}")
        print(f"Sniffer Dongle: {'✅ PASS' if sniffer_ok else '⚠️  SKIPPED' if not sniffer_port else '❌ FAIL'}")
        
        if mac_ok and sniffer_ok:
            print("\n🎉 Both interfaces are working correctly!")
        elif mac_ok:
            print("\n✅ MacBook BLE is working. Sniffer needs attention.")
        else:
            print("\n❌ Issues detected. Please check the errors above.")

async def main():
    test = DualInterfaceTest()
    await test.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)