#!/usr/bin/env python3
"""
Data Processing for BlueFusion UI
Handles data formatting and transformation for display
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from .data_models import PacketInfo
except ImportError:
    from data_models import PacketInfo


class DataProcessor:
    """Processes and formats data for UI display"""
    
    @staticmethod
    def format_device_list(devices: Dict[str, Any]) -> pd.DataFrame:
        """Format device list for display"""
        if "error" in devices:
            return pd.DataFrame({"Error": [devices["error"]]})
        
        all_devices = []
        
        for source, device_list in devices.items():
            for device in device_list:
                device["source"] = source
                all_devices.append(device)
        
        if not all_devices:
            return pd.DataFrame({"Info": ["No devices found"]})
        
        df = pd.DataFrame(all_devices)
        
        # Format columns for display
        if not df.empty:
            # Rename columns for better display
            column_mapping = {
                "address": "Address",
                "name": "Name",
                "rssi": "RSSI",
                "source": "Source",
                "last_seen": "Last Seen",
                "packet_count": "Packets"
            }
            
            # Only rename columns that exist
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            
            # Format timestamps if present
            if "Last Seen" in df.columns:
                df["Last Seen"] = df["Last Seen"].apply(self._format_timestamp)
            
            # Sort by RSSI if available
            if "RSSI" in df.columns:
                df = df.sort_values("RSSI", ascending=False)
        
        return df
    
    @staticmethod
    def format_packet_stream(packets: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format packet stream for display"""
        if not packets:
            return pd.DataFrame({"Info": ["No packets received yet"]})
        
        formatted_packets = []
        for packet in packets:
            packet_info = PacketInfo(
                timestamp=packet["timestamp"],
                source=packet["source"],
                address=packet["address"],
                packet_type=packet["packet_type"],
                rssi=packet["rssi"],
                data=packet.get("data")
            )
            formatted_packets.append(packet_info.to_display_dict())
        
        return pd.DataFrame(formatted_packets)
    
    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp
    
    @staticmethod
    def aggregate_device_data(device_data: Dict[str, Any]) -> pd.DataFrame:
        """Aggregate device data for summary display"""
        if not device_data:
            return pd.DataFrame({"Info": ["No device data available"]})
        
        devices = []
        for addr, data in device_data.items():
            devices.append({
                "Address": addr,
                "First Seen": DataProcessor._format_timestamp(data["first_seen"]),
                "Last Seen": DataProcessor._format_timestamp(data["last_seen"]),
                "RSSI": data.get("last_rssi", "N/A"),
                "Packets": data["packets"],
                "Sources": ", ".join(sorted(data["sources"]))
            })
        
        df = pd.DataFrame(devices)
        return df.sort_values("Packets", ascending=False)
    
    @staticmethod
    def calculate_packet_rates(packet_history: List[Dict[str, Any]], 
                             window_seconds: int = 60) -> Dict[str, float]:
        """Calculate packet rates over a time window"""
        if not packet_history:
            return {"total": 0.0, "macbook": 0.0, "sniffer": 0.0}
        
        now = datetime.now()
        window_start = now.timestamp() - window_seconds
        
        recent_packets = [
            p for p in packet_history 
            if datetime.fromisoformat(p["timestamp"]).timestamp() > window_start
        ]
        
        if not recent_packets:
            return {"total": 0.0, "macbook": 0.0, "sniffer": 0.0}
        
        total = len(recent_packets)
        macbook = sum(1 for p in recent_packets if p["source"] == "macbook_ble")
        sniffer = total - macbook
        
        return {
            "total": total / window_seconds,
            "macbook": macbook / window_seconds,
            "sniffer": sniffer / window_seconds
        }