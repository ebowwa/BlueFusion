#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner
from datetime import datetime

async def simple_ble_test():
    print("=== Simple BLE Test ===")
    print(f"Starting at {datetime.now()}\n")
    
    devices = {}
    
    def detection_callback(device, advertisement_data):
        devices[device.address] = device
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Found: {device.address} | {device.name or 'Unknown'} | RSSI: {advertisement_data.rssi}")
    
    scanner = BleakScanner(detection_callback)
    
    print("Starting scan for 10 seconds...")
    print("Make sure Bluetooth is enabled on your Mac!")
    print("-" * 50)
    
    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()
    
    print("-" * 50)
    print(f"\nScan complete! Found {len(devices)} devices.")
    
    if devices:
        print("\nDevice Summary:")
        for addr, device in devices.items():
            print(f"  • {addr} - {device.name or 'Unknown'}")

if __name__ == "__main__":
    asyncio.run(simple_ble_test())