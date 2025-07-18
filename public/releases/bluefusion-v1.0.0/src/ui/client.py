#!/usr/bin/env python3
"""
BlueFusion API Client
Handles HTTP communication with the BlueFusion API
"""
import httpx
from typing import Dict, Any, Optional


class BlueFusionClient:
    """Client for interacting with BlueFusion API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get interface status"""
        try:
            response = self.client.get(f"{self.base_url}/interfaces/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def start_scan(self, interface: str = "both", mode: str = "active") -> Dict[str, Any]:
        """Start scanning"""
        try:
            response = self.client.post(
                f"{self.base_url}/scan/start",
                json={"interface": interface, "mode": mode}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def stop_scan(self, interface: str = "both") -> Dict[str, Any]:
        """Stop scanning"""
        try:
            response = self.client.post(
                f"{self.base_url}/scan/stop",
                json={"interface": interface}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_devices(self, interface: str = "both") -> Dict[str, Any]:
        """Get discovered devices"""
        try:
            response = self.client.get(
                f"{self.base_url}/devices",
                params={"interface": interface}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def set_sniffer_channel(self, channel: int) -> Dict[str, Any]:
        """Set sniffer channel"""
        try:
            response = self.client.post(f"{self.base_url}/sniffer/channel/{channel}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def connect_device(self, address: str) -> Dict[str, Any]:
        """Connect to a device"""
        try:
            response = self.client.post(f"{self.base_url}/connect/{address}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def disconnect_device(self, address: str) -> Dict[str, Any]:
        """Disconnect from a device"""
        try:
            response = self.client.post(f"{self.base_url}/disconnect/{address}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def discover_services(self, address: str) -> Dict[str, Any]:
        """Discover services for a connected device"""
        try:
            response = self.client.get(f"{self.base_url}/devices/{address}/services")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def discover_characteristics(self, address: str, service_uuid: str) -> Dict[str, Any]:
        """Discover characteristics for a service"""
        try:
            response = self.client.get(f"{self.base_url}/devices/{address}/services/{service_uuid}/characteristics")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def discover_descriptors(self, address: str, char_uuid: str) -> Dict[str, Any]:
        """Discover descriptors for a characteristic"""
        try:
            response = self.client.get(f"{self.base_url}/devices/{address}/characteristics/{char_uuid}/descriptors")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def discover_all_services(self, address: str) -> Dict[str, Any]:
        """Trigger comprehensive service discovery"""
        try:
            response = self.client.post(f"{self.base_url}/devices/{address}/services/discover")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def read_characteristic(self, address: str, char_uuid: str) -> Dict[str, Any]:
        """Read a characteristic value"""
        try:
            response = self.client.get(f"{self.base_url}/devices/{address}/characteristics/{char_uuid}/read")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def write_characteristic(self, address: str, char_uuid: str, value: str, with_response: bool = True) -> Dict[str, Any]:
        """Write a value to a characteristic"""
        try:
            response = self.client.post(
                f"{self.base_url}/devices/{address}/characteristics/{char_uuid}/write",
                json={"value": value, "with_response": with_response}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup client on deletion"""
        if hasattr(self, 'client'):
            self.client.close()