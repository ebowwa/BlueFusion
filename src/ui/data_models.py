#!/usr/bin/env python3
"""
Data Models and Configuration for BlueFusion UI
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, Set
from datetime import datetime


# API Configuration
API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/stream"


@dataclass
class DeviceInfo:
    """Information about a discovered BLE device"""
    address: str
    first_seen: str
    last_seen: str
    last_rssi: Optional[int] = None
    packets: int = 0
    sources: Set[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = set()


@dataclass
class PacketInfo:
    """Information about a BLE packet"""
    timestamp: str
    source: str
    address: str
    packet_type: str
    rssi: int
    data: Optional[str] = None
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display"""
        return {
            "Time": datetime.fromisoformat(self.timestamp).strftime("%H:%M:%S.%f")[:-3],
            "Source": self.source,
            "Address": self.address[:8] + "...",
            "Type": self.packet_type,
            "RSSI": self.rssi,
            "Data Len": len(self.data or "") // 2
        }


@dataclass
class InterfaceStatus:
    """Status of a BLE interface"""
    initialized: bool = False
    scanning: bool = False
    connected: Optional[bool] = None
    port: Optional[str] = None
    
    def to_display_string(self, interface_name: str) -> str:
        """Convert to display string"""
        lines = [f"**{interface_name}**"]
        lines.append(f"- Initialized: {self.initialized}")
        lines.append(f"- Scanning: {self.scanning}")
        
        if self.connected is not None:
            lines.append(f"- Connected: {self.connected}")
        if self.port is not None:
            lines.append(f"- Port: {self.port}")
        
        return "\n".join(lines)


class ScanConfig:
    """Configuration for BLE scanning"""
    INTERFACES = ["Both", "MacBook", "Sniffer"]
    MODES = ["Active", "Passive"]
    DEFAULT_INTERFACE = "Both"
    DEFAULT_MODE = "Active"
    DEFAULT_CHANNEL = 37
    
    @staticmethod
    def normalize_interface(interface: str) -> str:
        """Normalize interface name for API"""
        return interface.lower()
    
    @staticmethod
    def normalize_mode(mode: str) -> str:
        """Normalize scan mode for API"""
        return mode.lower()