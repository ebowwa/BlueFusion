#!/usr/bin/env python3
"""
Interface Handlers for BlueFusion UI
Handles UI interactions and control logic
"""
from typing import Tuple, Optional

try:
    from .client import BlueFusionClient
    from .websocket_handler import WebSocketHandler
    from .data_models import InterfaceStatus, ScanConfig
except ImportError:
    from client import BlueFusionClient
    from websocket_handler import WebSocketHandler
    from data_models import InterfaceStatus, ScanConfig


class InterfaceHandlers:
    """Handles interface control and status operations"""
    
    def __init__(self, client: BlueFusionClient, ws_handler: WebSocketHandler):
        self.client = client
        self.ws_handler = ws_handler
    
    def get_interface_status(self) -> str:
        """Get current status of interfaces"""
        try:
            status = self.client.get_status()
            if "error" in status:
                return f"❌ API Error: {status['error']}\n\nMake sure the API server is running on http://localhost:8000"
            
            mac_status = InterfaceStatus(
                initialized=status.get("macbook", {}).get("initialized", False),
                scanning=status.get("macbook", {}).get("scanning", False)
            )
            
            snf_status = InterfaceStatus(
                initialized=status.get("sniffer", {}).get("initialized", False),
                scanning=status.get("sniffer", {}).get("scanning", False),
                connected=status.get("sniffer", {}).get("connected", False),
                port=status.get("sniffer", {}).get("port", "N/A")
            )
            
            return (
                mac_status.to_display_string("MacBook BLE") + 
                "\n\n" + 
                snf_status.to_display_string("Sniffer Dongle")
            )
        except Exception as e:
            return f"❌ Connection Error: {str(e)}\n\nCannot connect to API server at http://localhost:8000"
    
    def start_scanning(self, interface: str, mode: str) -> Tuple[str, str]:
        """Start BLE scanning"""
        try:
            normalized_interface = ScanConfig.normalize_interface(interface)
            normalized_mode = ScanConfig.normalize_mode(mode)
            
            result = self.client.start_scan(normalized_interface, normalized_mode)
            if "error" in result:
                return f"❌ Error: {result['error']}", self.get_interface_status()
            
            # Start WebSocket listener
            self.ws_handler.start()
            
            return f"✅ Started scanning on {interface} in {mode} mode", self.get_interface_status()
        except Exception as e:
            return f"❌ Connection Error: {str(e)}", "Cannot connect to API server"
    
    def stop_scanning(self, interface: str) -> Tuple[str, str]:
        """Stop BLE scanning"""
        normalized_interface = ScanConfig.normalize_interface(interface)
        
        result = self.client.stop_scan(normalized_interface)
        if "error" in result:
            return f"Error: {result['error']}", self.get_interface_status()
        
        return f"Stopped scanning on {interface}", self.get_interface_status()
    
    def set_channel(self, channel: int) -> str:
        """Set sniffer channel"""
        result = self.client.set_sniffer_channel(channel)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Sniffer channel set to {channel}"
    
    def format_statistics(self) -> str:
        """Format device statistics for display"""
        stats = self.ws_handler.get_device_stats()
        
        if not stats:
            return "No data collected yet"
        
        output = f"""**Overall Statistics**
Total unique devices: {stats['total_devices']}
Total packets captured: {stats['total_packets']}

**By Interface**
MacBook BLE devices: {stats['macbook_devices']}
Sniffer devices: {stats['sniffer_devices']}

**Top 5 Most Active Devices**"""
        
        for i, device in enumerate(stats['top_devices'], 1):
            output += f"\n{i}. {device['address']}: {device['packets']} packets (RSSI: {device['last_rssi']})"
        
        return output