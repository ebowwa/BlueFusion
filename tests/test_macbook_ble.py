#!/usr/bin/env python3
import asyncio
import sys
from datetime import datetime
from src.interfaces.macbook_ble import MacBookBLE

async def test_macbook_scanner():
    print("=== BlueFusion MacBook BLE Test ===")
    print(f"Starting at {datetime.now()}\n")
    
    # Create MacBook BLE interface
    mac_ble = MacBookBLE()
    
    # Initialize
    print("Initializing MacBook BLE interface...")
    await mac_ble.initialize()
    
    # Register a callback to see packets in real-time
    def packet_callback(packet):
        print(f"\n[PACKET] {packet.packet_type} from {packet.address}")
        print(f"  RSSI: {packet.rssi} dBm")
        if packet.metadata.get('name'):
            print(f"  Name: {packet.metadata['name']}")
        if packet.metadata.get('services'):
            print(f"  Services: {packet.metadata['services']}")
    
    mac_ble.register_callback(packet_callback)
    
    # Start scanning
    print("\nStarting BLE scan for 10 seconds...")
    print("You should see nearby BLE devices appear below:\n")
    await mac_ble.start_scanning()
    
    # Let it scan for 10 seconds
    await asyncio.sleep(10)
    
    # Stop scanning
    await mac_ble.stop_scanning()
    
    # Show discovered devices
    devices = await mac_ble.get_devices()
    print(f"\n\n=== SCAN COMPLETE ===")
    print(f"Found {len(devices)} devices:\n")
    
    for device in devices:
        print(f"Device: {device.address}")
        print(f"  Name: {device.name or 'Unknown'}")
        print(f"  RSSI: {device.rssi} dBm")
        if device.services:
            print(f"  Services: {device.services}")
        print()

if __name__ == "__main__":
    asyncio.run(test_macbook_scanner())