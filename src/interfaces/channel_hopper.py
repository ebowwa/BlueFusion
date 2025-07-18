#!/usr/bin/env python3
"""
Channel Hopping for BLE Sniffer
Implements automatic channel hopping to capture more packets
"""
import asyncio
from typing import Optional, List, Callable
from datetime import datetime, timedelta


class ChannelHopper:
    """Manages automatic channel hopping for BLE sniffers"""
    
    # BLE advertising channels
    ADVERTISING_CHANNELS = [37, 38, 39]
    
    # BLE data channels
    DATA_CHANNELS = list(range(0, 37))
    
    def __init__(self, sniffer_interface):
        self.sniffer = sniffer_interface
        self.hopping_enabled = False
        self.hop_interval = 0.1  # 100ms default
        self.channels: List[int] = self.ADVERTISING_CHANNELS
        self.current_channel_index = 0
        self.hop_task: Optional[asyncio.Task] = None
        self.stats = {
            "hops": 0,
            "start_time": None,
            "packets_per_channel": {ch: 0 for ch in range(40)}
        }
    
    async def start_hopping(self, channels: Optional[List[int]] = None, 
                          interval: float = 0.1):
        """Start automatic channel hopping"""
        if self.hopping_enabled:
            return
        
        self.channels = channels or self.ADVERTISING_CHANNELS
        self.hop_interval = interval
        self.hopping_enabled = True
        self.stats["start_time"] = datetime.now()
        
        # Start hopping task
        self.hop_task = asyncio.create_task(self._hop_loop())
    
    async def stop_hopping(self):
        """Stop channel hopping"""
        self.hopping_enabled = False
        if self.hop_task:
            self.hop_task.cancel()
            try:
                await self.hop_task
            except asyncio.CancelledError:
                pass
    
    async def _hop_loop(self):
        """Main hopping loop"""
        while self.hopping_enabled:
            try:
                # Set next channel
                current_channel = self.channels[self.current_channel_index]
                await self.sniffer.set_channel(current_channel)
                
                # Update stats
                self.stats["hops"] += 1
                
                # Wait for hop interval
                await asyncio.sleep(self.hop_interval)
                
                # Move to next channel
                self.current_channel_index = (self.current_channel_index + 1) % len(self.channels)
                
            except Exception as e:
                print(f"Channel hop error: {e}")
                await asyncio.sleep(self.hop_interval)
    
    def update_packet_stats(self, channel: int):
        """Update packet statistics for a channel"""
        if channel in self.stats["packets_per_channel"]:
            self.stats["packets_per_channel"][channel] += 1
    
    def get_hop_stats(self) -> dict:
        """Get hopping statistics"""
        if self.stats["start_time"]:
            duration = (datetime.now() - self.stats["start_time"]).total_seconds()
            hops_per_second = self.stats["hops"] / duration if duration > 0 else 0
        else:
            duration = 0
            hops_per_second = 0
        
        return {
            "enabled": self.hopping_enabled,
            "channels": self.channels,
            "current_channel": self.channels[self.current_channel_index] if self.channels else None,
            "hop_interval_ms": self.hop_interval * 1000,
            "total_hops": self.stats["hops"],
            "duration_seconds": duration,
            "hops_per_second": round(hops_per_second, 2),
            "packets_per_channel": self.stats["packets_per_channel"]
        }
    
    def set_advertising_mode(self):
        """Set hopping to advertising channels only"""
        self.channels = self.ADVERTISING_CHANNELS
    
    def set_data_mode(self):
        """Set hopping to data channels only"""
        self.channels = self.DATA_CHANNELS
    
    def set_all_channels_mode(self):
        """Set hopping to all BLE channels"""
        self.channels = list(range(40))
    
    def set_custom_channels(self, channels: List[int]):
        """Set custom channel list"""
        # Validate channels
        valid_channels = [ch for ch in channels if 0 <= ch <= 39]
        if valid_channels:
            self.channels = valid_channels


class SmartChannelHopper(ChannelHopper):
    """Intelligent channel hopping based on packet activity"""
    
    def __init__(self, sniffer_interface):
        super().__init__(sniffer_interface)
        self.channel_activity = {ch: 0 for ch in range(40)}
        self.adaptive_mode = False
        self.activity_window = 10  # seconds
        self.last_activity_check = datetime.now()
    
    async def start_adaptive_hopping(self, base_interval: float = 0.1):
        """Start adaptive channel hopping"""
        self.adaptive_mode = True
        await self.start_hopping(interval=base_interval)
    
    def update_channel_activity(self, channel: int):
        """Update channel activity for adaptive hopping"""
        self.channel_activity[channel] += 1
        self.update_packet_stats(channel)
        
        # Periodically adjust channels based on activity
        if (datetime.now() - self.last_activity_check).total_seconds() > self.activity_window:
            self._adjust_channels()
    
    def _adjust_channels(self):
        """Adjust channel list based on activity"""
        if not self.adaptive_mode:
            return
        
        # Sort channels by activity
        sorted_channels = sorted(
            self.channel_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Focus on top active channels plus advertising channels
        active_channels = [ch for ch, count in sorted_channels[:10] if count > 0]
        
        # Always include advertising channels
        for adv_ch in self.ADVERTISING_CHANNELS:
            if adv_ch not in active_channels:
                active_channels.append(adv_ch)
        
        if active_channels:
            self.channels = sorted(active_channels)
        
        # Reset activity counters
        self.channel_activity = {ch: 0 for ch in range(40)}
        self.last_activity_check = datetime.now()