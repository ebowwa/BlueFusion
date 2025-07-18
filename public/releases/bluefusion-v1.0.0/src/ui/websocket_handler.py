#!/usr/bin/env python3
"""
WebSocket Handler for BlueFusion
Manages real-time packet streaming via WebSocket
"""
import asyncio
import json
import websockets
import threading
import queue
from datetime import datetime
from typing import Dict, Any, Optional, Callable


class WebSocketHandler:
    """Handles WebSocket connection and packet streaming"""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/stream"):
        self.ws_url = ws_url
        self.packet_queue = queue.Queue()
        self.device_data = {}
        self.packet_history = []
        self.running = False
        self.thread = None
        self.packet_callback = None
    
    def set_packet_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback function for packet processing"""
        self.packet_callback = callback
    
    async def _websocket_listener(self):
        """Listen to WebSocket for real-time packets"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        packet = json.loads(message)
                        self.packet_queue.put(packet)
                        
                        # Update device data
                        self._update_device_data(packet)
                        
                        # Keep history limited
                        self.packet_history.append(packet)
                        if len(self.packet_history) > 1000:
                            self.packet_history.pop(0)
                        
                        # Call callback if set
                        if self.packet_callback:
                            self.packet_callback(packet)
                            
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        break
                        
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    def _update_device_data(self, packet: Dict[str, Any]):
        """Update device tracking data"""
        addr = packet["address"]
        if addr not in self.device_data:
            self.device_data[addr] = {
                "first_seen": packet["timestamp"],
                "packets": 0,
                "sources": set()
            }
        
        self.device_data[addr]["last_seen"] = packet["timestamp"]
        self.device_data[addr]["last_rssi"] = packet["rssi"]
        self.device_data[addr]["packets"] += 1
        self.device_data[addr]["sources"].add(packet["source"])
    
    def start(self):
        """Start WebSocket listener in background thread"""
        if self.running:
            return
        
        self.running = True
        
        def run():
            asyncio.new_event_loop().run_until_complete(self._websocket_listener())
        
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop WebSocket listener"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def get_packets(self, limit: int = 50) -> list:
        """Get packets from queue (consumes them)"""
        packets = []
        
        while not self.packet_queue.empty() and len(packets) < limit:
            try:
                packet = self.packet_queue.get_nowait()
                packets.append(packet)
            except queue.Empty:
                break
        
        return packets
    
    def get_recent_packets(self, limit: int = 50) -> list:
        """Get recent packets from history (non-consuming)"""
        # Return the most recent packets from history
        if limit >= len(self.packet_history):
            return list(self.packet_history)
        else:
            return list(self.packet_history[-limit:])
    
    def get_device_stats(self) -> Dict[str, Any]:
        """Get device statistics"""
        if not self.device_data:
            return {}
        
        total_devices = len(self.device_data)
        total_packets = sum(d["packets"] for d in self.device_data.values())
        
        mac_devices = sum(1 for d in self.device_data.values() if "macbook_ble" in d["sources"])
        snf_devices = sum(1 for d in self.device_data.values() if "sniffer_dongle" in d["sources"])
        
        return {
            "total_devices": total_devices,
            "total_packets": total_packets,
            "macbook_devices": mac_devices,
            "sniffer_devices": snf_devices,
            "top_devices": self._get_top_devices(5)
        }
    
    def _get_top_devices(self, count: int = 5) -> list:
        """Get top devices by packet count"""
        sorted_devices = sorted(
            self.device_data.items(),
            key=lambda x: x[1]["packets"],
            reverse=True
        )[:count]
        
        return [
            {
                "address": addr,
                "packets": data["packets"],
                "last_rssi": data.get("last_rssi", "N/A")
            }
            for addr, data in sorted_devices
        ]