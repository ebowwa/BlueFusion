#!/usr/bin/env python3
"""
Visualization Components for BlueFusion UI
Creates plots and charts for BLE data visualization
"""
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, Optional, List


class Visualizer:
    """Handles data visualization for BlueFusion UI"""
    
    @staticmethod
    def create_rssi_plot(device_data: Dict[str, Any], limit: int = 10) -> Optional[go.Figure]:
        """Create RSSI plot for top devices"""
        if not device_data:
            return None
        
        # Get top devices by packet count
        sorted_devices = sorted(
            device_data.items(),
            key=lambda x: x[1]["packets"],
            reverse=True
        )[:limit]
        
        fig = go.Figure()
        
        for addr, data in sorted_devices:
            if "last_rssi" in data:
                fig.add_trace(go.Bar(
                    x=[addr[:8] + "..."],
                    y=[data["last_rssi"]],
                    name=addr[:8] + "...",
                    text=f"{data['packets']} pkts",
                    textposition="auto"
                ))
        
        fig.update_layout(
            title="Device RSSI Levels",
            xaxis_title="Device Address",
            yaxis_title="RSSI (dBm)",
            showlegend=False,
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_activity_plot(packet_history: List[Dict[str, Any]], 
                           max_packets: int = 500) -> Optional[go.Figure]:
        """Create activity timeline plot"""
        if not packet_history:
            return None
        
        # Use last N packets
        recent_packets = packet_history[-max_packets:] if len(packet_history) > max_packets else packet_history
        
        # Group packets by timestamp (1 second bins)
        activity = {}
        for packet in recent_packets:
            timestamp = datetime.fromisoformat(packet["timestamp"])
            time_bin = timestamp.replace(microsecond=0)
            
            if time_bin not in activity:
                activity[time_bin] = {"macbook": 0, "sniffer": 0}
            
            source = "macbook" if packet["source"] == "macbook_ble" else "sniffer"
            activity[time_bin][source] += 1
        
        if not activity:
            return None
        
        times = sorted(activity.keys())
        mac_counts = [activity[t]["macbook"] for t in times]
        snf_counts = [activity[t]["sniffer"] for t in times]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=times,
            y=mac_counts,
            mode='lines+markers',
            name='MacBook BLE',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=times,
            y=snf_counts,
            mode='lines+markers',
            name='Sniffer',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="Packet Activity Timeline",
            xaxis_title="Time",
            yaxis_title="Packets/Second",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_channel_distribution_plot(packet_history: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create channel distribution plot"""
        if not packet_history:
            return None
        
        # Count packets by channel (if channel info is available)
        channel_counts = {}
        for packet in packet_history:
            channel = packet.get("channel", "Unknown")
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        if not channel_counts:
            return None
        
        channels = list(channel_counts.keys())
        counts = list(channel_counts.values())
        
        fig = go.Figure(data=[
            go.Bar(x=channels, y=counts)
        ])
        
        fig.update_layout(
            title="Packet Distribution by Channel",
            xaxis_title="BLE Channel",
            yaxis_title="Packet Count",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_packet_type_distribution(packet_history: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create packet type distribution pie chart"""
        if not packet_history:
            return None
        
        # Count packet types
        type_counts = {}
        for packet in packet_history:
            pkt_type = packet.get("packet_type", "Unknown")
            type_counts[pkt_type] = type_counts.get(pkt_type, 0) + 1
        
        if not type_counts:
            return None
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Packet Type Distribution",
            height=400
        )
        
        return fig