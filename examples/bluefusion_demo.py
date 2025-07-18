#!/usr/bin/env python3
"""
BlueFusion - AI-ready dual BLE interface controller
Demonstrates control over MacBook BLE and BLE sniffer dongle
"""
import asyncio
from bleak import BleakScanner
from datetime import datetime
import json

class BlueFusionController:
    def __init__(self):
        self.devices = {}
        self.packets = []
        
    async def scan_macbook_ble(self, duration=10):
        """Scan using MacBook's built-in BLE"""
        print(f"\n🔵 BlueFusion MacBook BLE Scanner")
        print(f"Scanning for {duration} seconds...\n")
        
        def callback(device, adv_data):
            self.devices[device.address] = {
                'name': device.name or 'Unknown',
                'rssi': adv_data.rssi,
                'services': list(adv_data.service_uuids),
                'timestamp': datetime.now().isoformat()
            }
            
            # AI-ready packet format
            packet = {
                'timestamp': datetime.now().isoformat(),
                'source': 'macbook_ble',
                'address': device.address,
                'rssi': adv_data.rssi,
                'type': 'advertisement',
                'data': {
                    'name': device.name,
                    'services': list(adv_data.service_uuids),
                    'manufacturer': dict(adv_data.manufacturer_data)
                }
            }
            self.packets.append(packet)
            
            print(f"📡 {device.address} | {device.name or 'Unknown':20} | {adv_data.rssi} dBm")
        
        scanner = BleakScanner(callback)
        await scanner.start()
        await asyncio.sleep(duration)
        await scanner.stop()
        
        return self.devices
    
    def export_for_ai(self):
        """Export data in AI-friendly format"""
        return {
            'scan_metadata': {
                'timestamp': datetime.now().isoformat(),
                'device_count': len(self.devices),
                'packet_count': len(self.packets)
            },
            'devices': self.devices,
            'packets': self.packets[-100:]  # Last 100 packets
        }

async def main():
    controller = BlueFusionController()
    
    # Scan with MacBook BLE
    devices = await controller.scan_macbook_ble(5)
    
    print(f"\n✅ Scan complete! Found {len(devices)} devices")
    
    # Export for AI analysis
    ai_data = controller.export_for_ai()
    
    print("\n🤖 AI-Ready Data Export:")
    print(f"  • Devices: {ai_data['scan_metadata']['device_count']}")
    print(f"  • Packets: {ai_data['scan_metadata']['packet_count']}")
    
    # Save to file for AI processing
    with open('bluefusion_scan.json', 'w') as f:
        json.dump(ai_data, f, indent=2)
    print(f"\n💾 Data saved to bluefusion_scan.json")

if __name__ == "__main__":
    print("🚀 BlueFusion - AI-Powered BLE Controller")
    print("=" * 50)
    asyncio.run(main())