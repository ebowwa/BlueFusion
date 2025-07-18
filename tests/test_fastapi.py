#!/usr/bin/env python3
"""
FastAPI test suite for BlueFusion API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.fastapi_server import app, mac_ble, sniffer
from src.interfaces.base import BLEDevice, BLEPacket, DeviceType
from datetime import datetime


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_mac_ble():
    """Mock MacBook BLE interface"""
    mock = AsyncMock()
    mock.is_running = False
    mock.initialize = AsyncMock()
    mock.start_scanning = AsyncMock()
    mock.stop_scanning = AsyncMock()
    mock.get_devices = AsyncMock(return_value=[
        BLEDevice(
            address="00:11:22:33:44:55",
            name="Test Device",
            rssi=-50,
            services=["180A", "180F"]
        )
    ])
    mock.connect = AsyncMock(return_value=True)
    mock.disconnect = AsyncMock()
    mock.read_characteristic = AsyncMock(return_value=b"test_data")
    return mock


@pytest.fixture
def mock_sniffer():
    """Mock Sniffer interface"""
    mock = AsyncMock()
    mock.is_running = False
    mock.serial_conn = MagicMock()
    mock.port = "/dev/cu.test"
    mock.initialize = AsyncMock()
    mock.start_scanning = AsyncMock()
    mock.stop_scanning = AsyncMock()
    mock.get_devices = AsyncMock(return_value=[
        BLEDevice(
            address="AA:BB:CC:DD:EE:FF",
            name=None,
            rssi=-60,
            raw_data=b"\x00\x01\x02\x03"
        )
    ])
    mock.set_channel = AsyncMock()
    mock.set_follow_mode = AsyncMock()
    return mock


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["api"] == "BlueFusion"
        assert "interfaces" in data
    
    def test_interfaces_status(self, client):
        """Test interfaces status endpoint"""
        response = client.get("/interfaces/status")
        assert response.status_code == 200
        data = response.json()
        assert "macbook" in data
        assert "sniffer" in data


class TestScanningEndpoints:
    """Test scanning control endpoints"""
    
    @patch('main.mac_ble')
    @patch('main.sniffer')
    def test_start_scanning_both(self, mock_sniff, mock_mac, client, mock_mac_ble, mock_sniffer):
        """Test starting scan on both interfaces"""
        mock_mac.__bool__.return_value = True
        mock_mac.start_scanning = mock_mac_ble.start_scanning
        mock_sniff.__bool__.return_value = True
        mock_sniff.serial_conn = mock_sniffer.serial_conn
        mock_sniff.start_scanning = mock_sniffer.start_scanning
        
        response = client.post("/scan/start", json={
            "interface": "both",
            "mode": "active"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scanning started"
        assert "macbook" in data["interfaces"]
        assert "sniffer" in data["interfaces"]
    
    @patch('main.mac_ble')
    def test_start_scanning_macbook_only(self, mock_mac, client, mock_mac_ble):
        """Test starting scan on MacBook only"""
        mock_mac.__bool__.return_value = True
        mock_mac.start_scanning = mock_mac_ble.start_scanning
        
        response = client.post("/scan/start", json={
            "interface": "macbook",
            "mode": "passive"
        })
        
        assert response.status_code == 200
        mock_mac_ble.start_scanning.assert_called_with(passive=True)
    
    @patch('main.mac_ble')
    @patch('main.sniffer')
    def test_stop_scanning(self, mock_sniff, mock_mac, client, mock_mac_ble, mock_sniffer):
        """Test stopping scan"""
        mock_mac.__bool__.return_value = True
        mock_mac.is_running = True
        mock_mac.stop_scanning = mock_mac_ble.stop_scanning
        mock_sniff.__bool__.return_value = True
        mock_sniff.is_running = True
        mock_sniff.stop_scanning = mock_sniffer.stop_scanning
        
        response = client.post("/scan/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scanning stopped"


class TestDeviceEndpoints:
    """Test device-related endpoints"""
    
    @patch('main.mac_ble')
    @patch('main.sniffer')
    def test_get_devices(self, mock_sniff, mock_mac, client, mock_mac_ble, mock_sniffer):
        """Test getting discovered devices"""
        mock_mac.__bool__.return_value = True
        mock_mac.get_devices = mock_mac_ble.get_devices
        mock_sniff.__bool__.return_value = True
        mock_sniff.get_devices = mock_sniffer.get_devices
        
        response = client.get("/devices")
        
        assert response.status_code == 200
        data = response.json()
        assert "macbook" in data
        assert "sniffer" in data
        assert len(data["macbook"]) == 1
        assert data["macbook"][0]["address"] == "00:11:22:33:44:55"
        assert data["macbook"][0]["name"] == "Test Device"
    
    @patch('main.mac_ble')
    def test_connect_device(self, mock_mac, client, mock_mac_ble):
        """Test connecting to a device"""
        mock_mac.__bool__.return_value = True
        mock_mac.connect = mock_mac_ble.connect
        
        response = client.post("/connect/00:11:22:33:44:55")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["address"] == "00:11:22:33:44:55"
    
    @patch('main.mac_ble')
    def test_disconnect_device(self, mock_mac, client, mock_mac_ble):
        """Test disconnecting from a device"""
        mock_mac.__bool__.return_value = True
        mock_mac.disconnect = mock_mac_ble.disconnect
        
        response = client.post("/disconnect/00:11:22:33:44:55")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
    
    @patch('main.mac_ble')
    def test_read_characteristic(self, mock_mac, client, mock_mac_ble):
        """Test reading a characteristic"""
        mock_mac.__bool__.return_value = True
        mock_mac.read_characteristic = mock_mac_ble.read_characteristic
        
        response = client.get("/read/00:11:22:33:44:55/00002a00-0000-1000-8000-00805f9b34fb")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == "746573745f64617461"  # hex of "test_data"
        assert data["length"] == 9


class TestSnifferEndpoints:
    """Test sniffer-specific endpoints"""
    
    @patch('main.sniffer')
    def test_set_channel(self, mock_sniff, client, mock_sniffer):
        """Test setting sniffer channel"""
        mock_sniff.__bool__.return_value = True
        mock_sniff.serial_conn = mock_sniffer.serial_conn
        mock_sniff.set_channel = mock_sniffer.set_channel
        
        response = client.post("/sniffer/channel/37")
        
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == 37
        mock_sniffer.set_channel.assert_called_with(37)
    
    @patch('main.sniffer')
    def test_set_channel_invalid(self, mock_sniff, client):
        """Test setting invalid channel"""
        mock_sniff.__bool__.return_value = True
        mock_sniff.serial_conn = MagicMock()
        
        response = client.post("/sniffer/channel/40")
        
        assert response.status_code == 400
        assert "Channel must be between 0-39" in response.json()["detail"]
    
    @patch('main.sniffer')
    def test_follow_device(self, mock_sniff, client, mock_sniffer):
        """Test following a device"""
        mock_sniff.__bool__.return_value = True
        mock_sniff.serial_conn = mock_sniffer.serial_conn
        mock_sniff.set_follow_mode = mock_sniffer.set_follow_mode
        
        response = client.post("/sniffer/follow/AA:BB:CC:DD:EE:FF")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "following device"
        mock_sniffer.set_follow_mode.assert_called_with("AA:BB:CC:DD:EE:FF")


class TestWebSocket:
    """Test WebSocket endpoint"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection"""
        with client.websocket_connect("/stream") as websocket:
            # Connection should be established
            # In a real test, we'd send packets and verify they're received
            websocket.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])