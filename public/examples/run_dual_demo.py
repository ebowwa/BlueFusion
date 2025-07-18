#!/usr/bin/env python3
"""
BlueFusion Dual Interface Demo
Shows both interfaces working together with proper data handling
"""
import asyncio
import sys
from datetime import datetime
from collections import defaultdict
import serial
import serial.tools.list_ports

# Import the actual interfaces
sys.path.append('/Users/ebowwa/apps/BlueFusion')
from src.interfaces.macbook_ble import MacBookBLE
from src.interfaces.sniffer_dongle import SnifferDongle

class DualBLEMonitor:
    def __init__(self):
        self.mac_ble = MacBookBLE()
        self.sniffer = SnifferDongle(port="/dev/cu.usbmodem101")  # Using detected port
        self.device_data = defaultdict(lambda: {
            'mac_seen': 0,
            'sniffer_seen': 0,
            'name': None,
            'last_rssi_mac': None,
            'last_rssi_sniffer': None,
            'services': set()
        })
        
    def handle_mac_packet(self, packet):
        """Handle packets from MacBook BLE"""
        addr = packet.address
        self.device_data[addr]['mac_seen'] += 1
        self.device_data[addr]['last_rssi_mac'] = packet.rssi
        
        if packet.metadata.get('name'):
            self.device_data[addr]['name'] = packet.metadata['name']
        
        if packet.metadata.get('services'):
            self.device_data[addr]['services'].update(packet.metadata['services'])
        
        print(f"[MAC] {packet.address[:8]}... | {packet.packet_type:12} | RSSI: {packet.rssi:4} | {packet.metadata.get('name', 'Unknown'):20}")
    
    def handle_sniffer_packet(self, packet):
        """Handle packets from Sniffer"""
        addr = packet.address
        self.device_data[addr]['sniffer_seen'] += 1
        self.device_data[addr]['last_rssi_sniffer'] = packet.rssi
        
        print(f"[SNF] {packet.address[:8]}... | {packet.packet_type:12} | RSSI: {packet.rssi:4} | Ch: {packet.metadata.get('channel', 'N/A'):2}")
    
    async def run_monitor(self, duration=30):
        """Run both interfaces simultaneously"""
        print(f"\n=== BlueFusion Dual BLE Monitor ===")
        print(f"Running for {duration} seconds...")
        print(f"Time: {datetime.now()}\n")
        
        # Register callbacks
        self.mac_ble.register_callback(self.handle_mac_packet)
        self.sniffer.register_callback(self.handle_sniffer_packet)
        
        # Initialize both interfaces
        print("Initializing interfaces...")
        await self.mac_ble.initialize()
        await self.sniffer.initialize()
        
        print("\nStarting dual monitoring...")
        print("-" * 80)
        print("Source | Address    | Type         | RSSI | Details")
        print("-" * 80)
        
        # Start both scanners
        await self.mac_ble.start_scanning()
        await self.sniffer.start_scanning(passive=True)
        
        # Monitor for specified duration
        await asyncio.sleep(duration)
        
        # Stop both scanners
        await self.mac_ble.stop_scanning()
        await self.sniffer.stop_scanning()
        
        # Display summary
        self.display_summary()
    
    def display_summary(self):
        """Display comprehensive summary of findings"""
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)
        
        # Sort devices by total packets seen
        sorted_devices = sorted(
            self.device_data.items(),
            key=lambda x: x[1]['mac_seen'] + x[1]['sniffer_seen'],
            reverse=True
        )
        
        print(f"\nTotal unique devices: {len(sorted_devices)}")
        print(f"\nTop 10 Most Active Devices:")
        print("-" * 80)
        print(f"{'Address':17} | {'Name':20} | {'MAC Pkts':8} | {'SNF Pkts':8} | {'MAC RSSI':8} | {'SNF RSSI':8}")
        print("-" * 80)
        
        for addr, data in sorted_devices[:10]:
            name = data['name'] or 'Unknown'
            mac_rssi = f"{data['last_rssi_mac']}" if data['last_rssi_mac'] else "N/A"
            snf_rssi = f"{data['last_rssi_sniffer']}" if data['last_rssi_sniffer'] else "N/A"
            
            print(f"{addr[:17]:17} | {name[:20]:20} | {data['mac_seen']:8} | {data['sniffer_seen']:8} | {mac_rssi:8} | {snf_rssi:8}")
        
        # Comparison statistics
        print(f"\n\nInterface Comparison:")
        print("-" * 40)
        
        mac_only = sum(1 for d in self.device_data.values() if d['mac_seen'] > 0 and d['sniffer_seen'] == 0)
        snf_only = sum(1 for d in self.device_data.values() if d['sniffer_seen'] > 0 and d['mac_seen'] == 0)
        both_seen = sum(1 for d in self.device_data.values() if d['mac_seen'] > 0 and d['sniffer_seen'] > 0)
        
        print(f"Devices seen by MacBook BLE only: {mac_only}")
        print(f"Devices seen by Sniffer only: {snf_only}")
        print(f"Devices seen by both: {both_seen}")
        
        total_mac_packets = sum(d['mac_seen'] for d in self.device_data.values())
        total_snf_packets = sum(d['sniffer_seen'] for d in self.device_data.values())
        
        print(f"\nTotal packets captured:")
        print(f"  MacBook BLE: {total_mac_packets}")
        print(f"  Sniffer: {total_snf_packets}")
        
        # Services discovered
        all_services = set()
        for data in self.device_data.values():
            all_services.update(data['services'])
        
        if all_services:
            print(f"\n\nUnique BLE Services Discovered: {len(all_services)}")
            for service in sorted(all_services)[:10]:
                print(f"  - {service}")
            if len(all_services) > 10:
                print(f"  ... and {len(all_services) - 10} more")

async def main():
    monitor = DualBLEMonitor()
    
    try:
        # Run for 10 seconds by default
        await monitor.run_monitor(duration=10)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("BlueFusion - Dual BLE Interface Demo")
    print("Press Ctrl+C to stop monitoring\n")
    
    asyncio.run(main())