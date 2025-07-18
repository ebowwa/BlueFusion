#!/usr/bin/env python3
"""
BlueFusion FastAPI Server
Provides REST API for dual BLE interface control
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.interfaces.macbook_ble import MacBookBLE
from src.interfaces.sniffer_dongle import SnifferDongle
from src.interfaces.base import BLEDevice, BLEPacket, DeviceType, BLEService, BLECharacteristic, BLEDescriptor
from src.interfaces.security_manager import SecurityManager, SecurityRequirements, SecurityLevel
from src.interfaces.auto_connect_manager import AutoConnectManager, ConnectionConfig, RetryStrategy, ConnectionMetrics
from src.utils.serial_utils import verify_serial_connection


class ScanMode(str, Enum):
    PASSIVE = "passive"
    ACTIVE = "active"


class InterfaceType(str, Enum):
    MACBOOK = "macbook"
    SNIFFER = "sniffer"
    BOTH = "both"


# Global interface instances
mac_ble: Optional[MacBookBLE] = None
sniffer: Optional[SnifferDongle] = None
security_manager: Optional[SecurityManager] = None
auto_connect_manager: Optional[AutoConnectManager] = None
active_connections: List[WebSocket] = []
pairing_queue: asyncio.Queue = asyncio.Queue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mac_ble, sniffer, security_manager, auto_connect_manager
    
    print("Initializing BLE interfaces...")
    
    # Initialize security manager
    security_manager = SecurityManager()
    
    # Register pairing callbacks
    async def handle_passkey_request(device_address: str, message: str) -> str:
        # Queue pairing request for UI
        await pairing_queue.put({
            "type": "passkey_request",
            "address": device_address,
            "message": message
        })
        # Wait for response (with timeout)
        # In real implementation, this would wait for UI response
        return "123456"  # Default passkey for now
    
    security_manager.register_pairing_callback("passkey_request", handle_passkey_request)
    
    # Initialize MacBook BLE with security manager
    try:
        mac_ble = MacBookBLE(security_manager)
        await mac_ble.initialize()
        print("✅ MacBook BLE initialized successfully")
    except Exception as e:
        print(f"⚠️ MacBook BLE initialization failed: {e}")
        mac_ble = None
    
    # Initialize Auto-Connect Manager if MacBook BLE is available
    if mac_ble:
        try:
            auto_connect_manager = AutoConnectManager(mac_ble)
            await auto_connect_manager.start()
            print("✅ Auto-Connect Manager initialized successfully")
        except Exception as e:
            print(f"⚠️ Auto-Connect Manager initialization failed: {e}")
            auto_connect_manager = None
    
    # Initialize Sniffer (auto-detect port) with security manager
    try:
        sniffer = SnifferDongle(security_manager=security_manager)
        await sniffer.initialize()
        if sniffer.serial_conn:
            print(f"✅ Sniffer initialized on port: {sniffer.port}")
        else:
            print("⚠️ No sniffer dongle detected")
    except Exception as e:
        print(f"⚠️ Sniffer initialization failed: {e}")
        sniffer = None
    
    print("BlueFusion API ready!")
    
    yield
    
    # Shutdown
    print("Shutting down BLE interfaces...")
    if auto_connect_manager:
        await auto_connect_manager.stop()
    if mac_ble and mac_ble.is_running:
        await mac_ble.stop_scanning()
    if sniffer and sniffer.is_running:
        await sniffer.stop_scanning()


app = FastAPI(
    title="BlueFusion API",
    description="Dual BLE Interface Controller - MacBook BLE + Sniffer Dongle",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS to allow Gradio frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7860", "http://127.0.0.1:7860", "*"],  # Gradio typically runs on 7860
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "status": "online",
        "api": "BlueFusion",
        "version": "0.1.0",
        "interfaces": {
            "macbook": {
                "initialized": mac_ble is not None,
                "scanning": mac_ble.is_running if mac_ble else False,
                "status": "ready" if mac_ble else "not initialized"
            },
            "sniffer": {
                "initialized": sniffer is not None,
                "connected": sniffer.serial_conn is not None if sniffer else False,
                "port": sniffer.port if sniffer else None,
                "scanning": sniffer.is_running if sniffer else False,
                "status": "connected" if (sniffer and sniffer.serial_conn) else "no dongle detected"
            }
        }
    }


@app.get("/interfaces/status")
async def get_interfaces_status():
    """Get status of both BLE interfaces"""
    return {
        "macbook": {
            "initialized": mac_ble is not None,
            "scanning": mac_ble.is_running if mac_ble else False
        },
        "sniffer": {
            "initialized": sniffer is not None,
            "connected": sniffer.is_connected() if sniffer else False,
            "port": sniffer.port if sniffer else None,
            "scanning": sniffer.is_running if sniffer else False
        }
    }


@app.post("/scan/start")
async def start_scanning(
    interface: InterfaceType = InterfaceType.BOTH,
    mode: ScanMode = ScanMode.ACTIVE
):
    """Start BLE scanning on specified interface(s)"""
    results = {}
    
    if interface in [InterfaceType.MACBOOK, InterfaceType.BOTH]:
        if not mac_ble:
            raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
        
        await mac_ble.start_scanning(passive=(mode == ScanMode.PASSIVE))
        results["macbook"] = "started"
    
    if interface in [InterfaceType.SNIFFER, InterfaceType.BOTH]:
        if not sniffer or not sniffer.serial_conn:
            raise HTTPException(status_code=503, detail="Sniffer not connected")
        
        await sniffer.start_scanning(passive=(mode == ScanMode.PASSIVE))
        results["sniffer"] = "started"
    
    return {"status": "scanning started", "interfaces": results}


@app.post("/scan/stop")
async def stop_scanning(interface: InterfaceType = InterfaceType.BOTH):
    """Stop BLE scanning on specified interface(s)"""
    results = {}
    
    if interface in [InterfaceType.MACBOOK, InterfaceType.BOTH]:
        if mac_ble and mac_ble.is_running:
            await mac_ble.stop_scanning()
            results["macbook"] = "stopped"
    
    if interface in [InterfaceType.SNIFFER, InterfaceType.BOTH]:
        if sniffer and sniffer.is_running:
            await sniffer.stop_scanning()
            results["sniffer"] = "stopped"
    
    return {"status": "scanning stopped", "interfaces": results}


@app.get("/devices")
async def get_devices(interface: InterfaceType = InterfaceType.BOTH):
    """Get list of discovered devices"""
    devices = {}
    
    if interface in [InterfaceType.MACBOOK, InterfaceType.BOTH]:
        if mac_ble:
            mac_devices = await mac_ble.get_devices()
            devices["macbook"] = [
                {
                    "address": d.address,
                    "name": d.name,
                    "rssi": d.rssi,
                    "services": d.services,
                    "manufacturer_data": {str(k): v.hex() if isinstance(v, bytes) else v 
                                        for k, v in d.manufacturer_data.items()} if d.manufacturer_data else {}
                }
                for d in mac_devices
            ]
    
    if interface in [InterfaceType.SNIFFER, InterfaceType.BOTH]:
        if sniffer:
            sniff_devices = await sniffer.get_devices()
            devices["sniffer"] = [
                {
                    "address": d.address,
                    "name": d.name,
                    "rssi": d.rssi,
                    "raw_data": d.raw_data.hex() if d.raw_data else None
                }
                for d in sniff_devices
            ]
    
    return devices


@app.post("/connect/{address}")
async def connect_device(address: str):
    """Connect to a BLE device (MacBook interface only)"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    success = await mac_ble.connect(address)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect to device")
    
    return {"status": "connected", "address": address}


@app.post("/disconnect/{address}")
async def disconnect_device(address: str):
    """Disconnect from a BLE device"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    await mac_ble.disconnect(address)
    return {"status": "disconnected", "address": address}


@app.get("/read/{address}/{char_uuid}")
async def read_characteristic(address: str, char_uuid: str):
    """Read a GATT characteristic from a connected device"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    data = await mac_ble.read_characteristic(address, char_uuid)
    if data is None:
        raise HTTPException(status_code=400, detail="Failed to read characteristic")
    
    return {
        "address": address,
        "characteristic": char_uuid,
        "data": data.hex(),
        "length": len(data)
    }


@app.get("/devices/{address}/services")
async def discover_services(address: str):
    """Discover GATT services for a connected device"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    services = await mac_ble.discover_services(address)
    if not services:
        raise HTTPException(status_code=400, detail="Failed to discover services or device not connected")
    
    return {
        "address": address,
        "services": [
            {
                "uuid": service.uuid,
                "handle": service.handle,
                "primary": service.primary
            }
            for service in services
        ],
        "count": len(services)
    }


@app.get("/devices/{address}/services/{service_uuid}/characteristics")
async def discover_characteristics(address: str, service_uuid: str):
    """Discover characteristics for a specific service"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    characteristics = await mac_ble.discover_characteristics(address, service_uuid)
    if not characteristics:
        raise HTTPException(status_code=400, detail="Failed to discover characteristics or service not found")
    
    return {
        "address": address,
        "service_uuid": service_uuid,
        "characteristics": [
            {
                "uuid": char.uuid,
                "handle": char.handle,
                "properties": char.properties
            }
            for char in characteristics
        ],
        "count": len(characteristics)
    }


@app.get("/devices/{address}/characteristics/{char_uuid}/descriptors")
async def discover_descriptors(address: str, char_uuid: str):
    """Discover descriptors for a specific characteristic"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    descriptors = await mac_ble.discover_descriptors(address, char_uuid)
    if not descriptors:
        raise HTTPException(status_code=400, detail="Failed to discover descriptors or characteristic not found")
    
    return {
        "address": address,
        "characteristic_uuid": char_uuid,
        "descriptors": [
            {
                "uuid": desc.uuid,
                "handle": desc.handle
            }
            for desc in descriptors
        ],
        "count": len(descriptors)
    }


@app.post("/devices/{address}/services/discover")
async def discover_all_services(address: str):
    """Trigger comprehensive service discovery for a device"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE not initialized")
    
    # First discover services
    services = await mac_ble.discover_services(address)
    if not services:
        raise HTTPException(status_code=400, detail="Failed to discover services or device not connected")
    
    # Then discover characteristics for each service
    detailed_services = []
    for service in services:
        characteristics = await mac_ble.discover_characteristics(address, service.uuid)
        
        # Discover descriptors for each characteristic
        detailed_characteristics = []
        for char in characteristics:
            descriptors = await mac_ble.discover_descriptors(address, char.uuid)
            detailed_characteristics.append({
                "uuid": char.uuid,
                "handle": char.handle,
                "properties": char.properties,
                "descriptors": [
                    {
                        "uuid": desc.uuid,
                        "handle": desc.handle
                    }
                    for desc in descriptors
                ]
            })
        
        detailed_services.append({
            "uuid": service.uuid,
            "handle": service.handle,
            "primary": service.primary,
            "characteristics": detailed_characteristics
        })
    
    return {
        "address": address,
        "services": detailed_services,
        "services_count": len(detailed_services),
        "total_characteristics": sum(len(s["characteristics"]) for s in detailed_services),
        "total_descriptors": sum(len(c["descriptors"]) for s in detailed_services for c in s["characteristics"])
    }


@app.get("/devices/{address}/characteristics/{char_uuid}/read")
async def read_characteristic(address: str, char_uuid: str):
    """Read a characteristic value"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE interface not available")
    
    try:
        value = await mac_ble.read_characteristic(address, char_uuid)
        if value is None:
            raise HTTPException(status_code=400, detail="Failed to read characteristic")
        
        return {
            "address": address,
            "characteristic": char_uuid,
            "value": value.hex(),
            "length": len(value)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read failed: {str(e)}")


@app.post("/devices/{address}/characteristics/{char_uuid}/write")
async def write_characteristic(address: str, char_uuid: str, request: dict):
    """Write a value to a characteristic"""
    if not mac_ble:
        raise HTTPException(status_code=503, detail="MacBook BLE interface not available")
    
    try:
        # Get value from request body
        value_hex = request.get("value", "")
        with_response = request.get("with_response", True)
        
        # Convert hex string to bytes
        try:
            value_bytes = bytes.fromhex(value_hex)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hex value")
        
        success = await mac_ble.write_characteristic(address, char_uuid, value_bytes, with_response)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to write characteristic")
        
        return {
            "address": address,
            "characteristic": char_uuid,
            "value": value_hex,
            "with_response": with_response,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Write failed: {str(e)}")


@app.post("/sniffer/channel/{channel}")
async def set_sniffer_channel(channel: int):
    """Set the BLE channel for the sniffer (0-39)"""
    if not sniffer or not sniffer.serial_conn:
        raise HTTPException(status_code=503, detail="Sniffer not connected")
    
    if not 0 <= channel <= 39:
        raise HTTPException(status_code=400, detail="Channel must be between 0-39")
    
    await sniffer.set_channel(channel)
    return {"status": "channel set", "channel": channel}


@app.post("/sniffer/follow/{address}")
async def follow_device(address: str):
    """Configure sniffer to follow a specific device"""
    if not sniffer or not sniffer.serial_conn:
        raise HTTPException(status_code=503, detail="Sniffer not connected")
    
    await sniffer.set_follow_mode(address)
    return {"status": "following device", "address": address}


@app.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time packet streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    # Packet handler that sends to WebSocket
    async def send_packet(packet: BLEPacket):
        try:
            packet_data = {
                "timestamp": packet.timestamp.isoformat(),
                "source": packet.source.value,
                "address": packet.address,
                "rssi": packet.rssi,
                "packet_type": packet.packet_type,
                "data": packet.data.hex() if packet.data else "",
                "metadata": packet.metadata
            }
            await websocket.send_json(packet_data)
        except:
            pass
    
    # Register callbacks
    if mac_ble:
        mac_ble.register_callback(lambda p: asyncio.create_task(send_packet(p)))
    if sniffer:
        sniffer.register_callback(lambda p: asyncio.create_task(send_packet(p)))
    
    try:
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client commands if needed
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/stats")
async def get_statistics():
    """Get packet statistics from both interfaces"""
    # This would need to be implemented in the interface classes
    # For now, return a placeholder
    return {
        "message": "Statistics endpoint - to be implemented",
        "active_websockets": len(active_connections)
    }


@app.get("/security/bonds")
async def get_bonded_devices():
    """Get list of bonded devices"""
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
    
    bonds = {}
    for address, bond_info in security_manager.bonds.items():
        bonds[address] = {
            "security_level": bond_info.security_level.value,
            "authenticated": bond_info.authenticated
        }
    
    return bonds


@app.delete("/security/bonds/{address}")
async def remove_bond(address: str):
    """Remove bond with a device"""
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
    
    if security_manager.remove_bond(address):
        return {"status": "success", "message": f"Bond removed for {address}"}
    else:
        raise HTTPException(status_code=404, detail=f"No bond found for {address}")


@app.post("/security/pair/{address}")
async def pair_device(address: str):
    """Initiate pairing with a device"""
    if not security_manager:
        raise HTTPException(status_code=503, detail="Security manager not initialized")
    
    # Check which interface can handle this device
    if mac_ble and address in [d.address for d in await mac_ble.get_devices()]:
        success = await mac_ble.pair_device(address)
        return {
            "status": "success" if success else "failed",
            "interface": "macbook_ble"
        }
    
    raise HTTPException(status_code=404, detail="Device not found")


@app.get("/security/pairing/pending")
async def get_pending_pairings():
    """Get pending pairing requests"""
    pending = []
    try:
        while not pairing_queue.empty():
            pending.append(pairing_queue.get_nowait())
    except asyncio.QueueEmpty:
        pass
    
    return {"pending": pending}


@app.post("/security/pairing/respond")
async def respond_to_pairing(address: str, response: str):
    """Respond to a pairing request"""
    # In a real implementation, this would communicate back to the security manager
    # For now, we'll just acknowledge
    return {
        "status": "success",
        "message": f"Pairing response recorded for {address}"
    }


@app.get("/sniffer/channel/stats")
async def get_channel_stats():
    """Get channel hopping statistics"""
    if not sniffer or not sniffer.channel_hopper:
        raise HTTPException(status_code=404, detail="Sniffer or channel hopper not available")
    
    stats = sniffer.channel_hopper.get_hop_stats()
    return {
        "channel_hopping": stats,
        "current_channel": sniffer.current_channel,
        "total_discovered_devices": len(sniffer.discovered_devices)
    }


@app.post("/sniffer/channel/hopping/{enabled}")
async def toggle_channel_hopping(enabled: bool):
    """Enable or disable channel hopping"""
    if not sniffer:
        raise HTTPException(status_code=404, detail="Sniffer not available")
    
    if enabled:
        if not sniffer.channel_hopper:
            from src.interfaces.channel_hopper import SmartChannelHopper
            sniffer.channel_hopper = SmartChannelHopper(sniffer)
        
        await sniffer.channel_hopper.start_adaptive_hopping()
        return {"status": "success", "message": "Channel hopping enabled"}
    else:
        if sniffer.channel_hopper:
            await sniffer.channel_hopper.stop_hopping()
        return {"status": "success", "message": "Channel hopping disabled"}


# Auto-Connect Manager Endpoints
@app.get("/auto-connect/status")
async def get_auto_connect_status():
    """Get Auto-Connect Manager status and all managed connections"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    return {
        "manager_running": auto_connect_manager._running,
        "connections": auto_connect_manager.get_all_connections_status()
    }


@app.get("/auto-connect/devices/{address}/status")
async def get_device_auto_connect_status(address: str):
    """Get auto-connect status for a specific device"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    status = auto_connect_manager.get_connection_status(address)
    if not status:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    return status


@app.post("/auto-connect/devices/{address}/add")
async def add_device_to_auto_connect(
    address: str,
    max_retries: int = 5,
    initial_retry_delay: float = 1.0,
    max_retry_delay: float = 60.0,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    connection_timeout: float = 30.0,
    reconnect_on_failure: bool = True,
    health_check_interval: float = 30.0,
    stability_check_interval: float = 10.0,
    max_consecutive_failures: int = 3
):
    """Add a device to auto-connect management with custom configuration"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    config = ConnectionConfig(
        max_retries=max_retries,
        initial_retry_delay=initial_retry_delay,
        max_retry_delay=max_retry_delay,
        retry_strategy=retry_strategy,
        connection_timeout=connection_timeout,
        reconnect_on_failure=reconnect_on_failure,
        health_check_interval=health_check_interval,
        stability_check_interval=stability_check_interval,
        max_consecutive_failures=max_consecutive_failures
    )
    
    auto_connect_manager.add_managed_device(address, config)
    
    return {
        "status": "success",
        "message": f"Device {address} added to auto-connect management",
        "config": config.__dict__
    }


@app.delete("/auto-connect/devices/{address}")
async def remove_device_from_auto_connect(address: str):
    """Remove a device from auto-connect management"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    auto_connect_manager.remove_managed_device(address)
    
    return {
        "status": "success",
        "message": f"Device {address} removed from auto-connect management"
    }


@app.post("/auto-connect/devices/{address}/enable")
async def enable_device_auto_connect(address: str):
    """Enable auto-connect for a specific device"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    auto_connect_manager.enable_device(address)
    
    return {
        "status": "success",
        "message": f"Auto-connect enabled for device {address}"
    }


@app.post("/auto-connect/devices/{address}/disable")
async def disable_device_auto_connect(address: str):
    """Disable auto-connect for a specific device"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    auto_connect_manager.disable_device(address)
    
    return {
        "status": "success",
        "message": f"Auto-connect disabled for device {address}"
    }


@app.post("/auto-connect/devices/{address}/pause")
async def pause_device_auto_connect(address: str, duration: float = 60.0):
    """Pause auto-connect for a specific device for a specified duration (seconds)"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    auto_connect_manager.pause_device(address, duration)
    
    return {
        "status": "success",
        "message": f"Auto-connect paused for device {address} for {duration} seconds"
    }


@app.get("/auto-connect/devices/{address}/metrics")
async def get_device_connection_metrics(address: str):
    """Get detailed connection metrics for a specific device"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    connection = auto_connect_manager.managed_connections[address]
    
    return {
        "address": address,
        "metrics": connection.metrics.model_dump(),
        "current_state": connection.state.value,
        "retry_count": connection.retry_count,
        "enabled": connection.is_enabled,
        "next_retry_delay": connection.calculate_retry_delay() if connection.retry_count > 0 else 0,
        "paused_until": connection.pause_until.isoformat() if connection.pause_until else None
    }


@app.post("/auto-connect/devices/{address}/reset-metrics")
async def reset_device_connection_metrics(address: str):
    """Reset connection metrics for a specific device"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    if address not in auto_connect_manager.managed_connections:
        raise HTTPException(status_code=404, detail="Device not found in auto-connect manager")
    
    connection = auto_connect_manager.managed_connections[address]
    connection.metrics = ConnectionMetrics()
    connection.retry_count = 0
    
    return {
        "status": "success",
        "message": f"Connection metrics reset for device {address}"
    }


@app.get("/auto-connect/events")
async def get_auto_connect_events():
    """Get recent auto-connect events (this would typically be stored in a log)"""
    if not auto_connect_manager:
        raise HTTPException(status_code=503, detail="Auto-Connect Manager not initialized")
    
    # This is a placeholder - in a real implementation, you'd want to store events
    return {
        "message": "Event logging not implemented yet",
        "suggestion": "Use WebSocket endpoint for real-time events"
    }


@app.websocket("/auto-connect/events/stream")
async def auto_connect_events_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time auto-connect events"""
    await websocket.accept()
    
    if not auto_connect_manager:
        await websocket.close(code=1011, reason="Auto-Connect Manager not initialized")
        return
    
    events_queue = asyncio.Queue()
    
    def event_handler(address: str, event_type: str, data: Dict[str, Any]):
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "address": address,
                "event_type": event_type,
                "data": data
            }
            asyncio.create_task(events_queue.put(event))
        except Exception as e:
            print(f"Error in event handler: {e}")
    
    # Register event callback
    auto_connect_manager.register_event_callback(event_handler)
    
    try:
        while True:
            # Send events to WebSocket client
            event = await events_queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up - remove callback (in real implementation)
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )