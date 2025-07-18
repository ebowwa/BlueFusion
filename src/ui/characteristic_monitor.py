"""
Characteristic Value Monitor - Real-time monitoring and pattern analysis
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gradio as gr
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime
import asyncio

try:
    # Try relative imports first (when used as a module)
    from ..analyzers.hex_pattern_matcher import HexPatternMatcher, PatternMatch
except ImportError:
    # Fall back to absolute imports (when run directly)
    from src.analyzers.hex_pattern_matcher import HexPatternMatcher, PatternMatch


class CharacteristicMonitor:
    """Monitor and analyze BLE characteristic values in real-time"""
    
    def __init__(self, client):
        self.client = client
        self.pattern_matcher = HexPatternMatcher()
        self.monitoring_data = {}  # Store monitoring sessions
        self.value_history = {}  # Store value history per characteristic
        
    def create_interface(self):
        """Create the Characteristic Monitor UI interface"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Characteristic Selection")
                
                # Device and characteristic selection
                device_address = gr.Textbox(
                    label="Device Address",
                    placeholder="Enter device address",
                    info="Connected device address"
                )
                
                char_uuid = gr.Textbox(
                    label="Characteristic UUID",
                    placeholder="Enter characteristic UUID",
                    info="UUID to monitor"
                )
                
                # Monitoring controls
                gr.Markdown("### Monitoring Controls")
                with gr.Row():
                    read_once_btn = gr.Button("📖 Read Once", variant="secondary")
                    start_monitor_btn = gr.Button("▶️ Start Monitoring", variant="primary")
                    stop_monitor_btn = gr.Button("⏹️ Stop Monitoring", variant="stop")
                
                monitor_interval = gr.Slider(
                    label="Monitor Interval (seconds)",
                    minimum=0.1,
                    maximum=10.0,
                    value=1.0,
                    step=0.1
                )
                
                # Pattern matcher settings
                gr.Markdown("### Pattern Detection Settings")
                min_pattern_length = gr.Slider(
                    label="Minimum Pattern Length",
                    minimum=1,
                    maximum=16,
                    value=2,
                    step=1
                )
                
                max_pattern_length = gr.Slider(
                    label="Maximum Pattern Length",
                    minimum=2,
                    maximum=64,
                    value=32,
                    step=1
                )
                
                # History settings
                gr.Markdown("### History Settings")
                history_limit = gr.Number(
                    label="History Limit",
                    value=100,
                    minimum=10,
                    maximum=1000
                )
                
                clear_history_btn = gr.Button("🗑️ Clear History", variant="secondary")
                
            with gr.Column(scale=2):
                gr.Markdown("### Value Display")
                
                with gr.Tabs():
                    with gr.Tab("Current Value"):
                        current_value_display = gr.Textbox(
                            label="Current Value",
                            value="No data",
                            lines=5,
                            max_lines=10
                        )
                        
                        value_info = gr.JSON(
                            label="Value Information",
                            value={}
                        )
                        
                    with gr.Tab("Pattern Analysis"):
                        pattern_summary = gr.Markdown("**Pattern Analysis**\n\nNo patterns detected")
                        
                        patterns_display = gr.JSON(
                            label="Detected Patterns",
                            value=[]
                        )
                        
                        pattern_visualization = gr.Textbox(
                            label="Pattern Visualization",
                            value="",
                            lines=5,
                            max_lines=10
                        )
                        
                    with gr.Tab("Value History"):
                        history_display = gr.DataFrame(
                            headers=["Timestamp", "Hex Value", "ASCII", "Length", "Change"],
                            value=[],
                            label="Value History"
                        )
                        
                    with gr.Tab("Advanced Analysis"):
                        sequence_analysis = gr.JSON(
                            label="Sequence Analysis",
                            value={}
                        )
                        
                        encoding_detection = gr.JSON(
                            label="Encoding Detection",
                            value={}
                        )
                        
                        bit_patterns = gr.JSON(
                            label="Bit-level Patterns",
                            value=[]
                        )
                        
                # Status
                monitor_status = gr.Markdown("**Status:** Not monitoring")
        
        # Event handlers
        read_once_btn.click(
            self.read_characteristic_once,
            inputs=[device_address, char_uuid, min_pattern_length, max_pattern_length],
            outputs=[
                current_value_display, value_info, pattern_summary, patterns_display,
                pattern_visualization, sequence_analysis, encoding_detection, bit_patterns,
                monitor_status
            ]
        )
        
        start_monitor_btn.click(
            self.start_monitoring,
            inputs=[device_address, char_uuid, monitor_interval, history_limit],
            outputs=[monitor_status]
        )
        
        stop_monitor_btn.click(
            self.stop_monitoring,
            inputs=[device_address, char_uuid],
            outputs=[monitor_status]
        )
        
        clear_history_btn.click(
            self.clear_history,
            inputs=[device_address, char_uuid],
            outputs=[history_display, monitor_status]
        )
        
        # Auto-refresh for monitoring
        monitor_timer = gr.Timer(1.0)
        monitor_timer.tick(
            self.update_monitor_display,
            inputs=[device_address, char_uuid, min_pattern_length, max_pattern_length],
            outputs=[
                current_value_display, value_info, pattern_summary, patterns_display,
                pattern_visualization, history_display, sequence_analysis, 
                encoding_detection, bit_patterns
            ]
        )
        
        return [
            device_address, char_uuid, read_once_btn, start_monitor_btn,
            stop_monitor_btn, monitor_interval, min_pattern_length, max_pattern_length,
            history_limit, clear_history_btn, current_value_display, value_info,
            pattern_summary, patterns_display, pattern_visualization, history_display,
            sequence_analysis, encoding_detection, bit_patterns, monitor_status
        ]
    
    def read_characteristic_once(self, address: str, char_uuid: str, 
                                min_pattern_len: int, max_pattern_len: int) -> Tuple:
        """Read characteristic value once and analyze"""
        if not address or not char_uuid:
            return (
                "No data", {}, "**Pattern Analysis**\n\nPlease provide device address and characteristic UUID",
                [], "", {}, {}, [], "**Status:** Missing parameters"
            )
        
        try:
            # Read characteristic
            result = self.client.read_characteristic(address, char_uuid)
            
            if "error" in result:
                error_msg = f"Error: {result['error']}"
                return (
                    error_msg, {}, f"**Pattern Analysis**\n\n{error_msg}",
                    [], "", {}, {}, [], f"**Status:** ❌ {error_msg}"
                )
            
            # Get the raw value
            raw_value = result.get("value", b"")
            if isinstance(raw_value, str):
                # Convert hex string to bytes
                raw_value = bytes.fromhex(raw_value)
            
            # Analyze the value
            analysis_result = self._analyze_value(raw_value, min_pattern_len, max_pattern_len)
            
            # Format displays
            current_display = self._format_hex_display(raw_value)
            value_info = self._create_value_info(raw_value)
            pattern_summary = self._create_pattern_summary(analysis_result["patterns"])
            pattern_viz = self._create_pattern_visualization(raw_value, analysis_result["patterns"])
            
            return (
                current_display,
                value_info,
                pattern_summary,
                analysis_result["patterns"].patterns if analysis_result["patterns"] else [],
                pattern_viz,
                analysis_result["sequences"],
                analysis_result["encodings"],
                analysis_result["bit_patterns"],
                f"**Status:** ✅ Read successful at {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            return (
                error_msg, {}, f"**Pattern Analysis**\n\n{error_msg}",
                [], "", {}, {}, [], f"**Status:** ❌ {error_msg}"
            )
    
    def start_monitoring(self, address: str, char_uuid: str, interval: float, history_limit: int) -> str:
        """Start monitoring a characteristic"""
        if not address or not char_uuid:
            return "**Status:** ❌ Please provide device address and characteristic UUID"
        
        key = f"{address}:{char_uuid}"
        
        # Initialize monitoring session
        self.monitoring_data[key] = {
            "active": True,
            "interval": interval,
            "last_read": None
        }
        
        # Initialize history if needed
        if key not in self.value_history:
            self.value_history[key] = {
                "values": [],
                "limit": int(history_limit)
            }
        
        return f"**Status:** ▶️ Monitoring {char_uuid} every {interval}s"
    
    def stop_monitoring(self, address: str, char_uuid: str) -> str:
        """Stop monitoring a characteristic"""
        if not address or not char_uuid:
            return "**Status:** ❌ Please provide device address and characteristic UUID"
        
        key = f"{address}:{char_uuid}"
        
        if key in self.monitoring_data:
            self.monitoring_data[key]["active"] = False
            return f"**Status:** ⏹️ Stopped monitoring {char_uuid}"
        
        return "**Status:** ℹ️ Not currently monitoring this characteristic"
    
    def clear_history(self, address: str, char_uuid: str) -> Tuple[List, str]:
        """Clear value history"""
        if not address or not char_uuid:
            return [], "**Status:** ❌ Please provide device address and characteristic UUID"
        
        key = f"{address}:{char_uuid}"
        
        if key in self.value_history:
            self.value_history[key]["values"] = []
            return [], f"**Status:** 🗑️ History cleared for {char_uuid}"
        
        return [], "**Status:** ℹ️ No history to clear"
    
    def update_monitor_display(self, address: str, char_uuid: str,
                             min_pattern_len: int, max_pattern_len: int) -> Tuple:
        """Update display for active monitoring"""
        if not address or not char_uuid:
            return ("No data", {}, "**Pattern Analysis**\n\nNo active monitoring",
                   [], "", [], {}, {}, [])
        
        key = f"{address}:{char_uuid}"
        
        # Check if monitoring is active
        if key not in self.monitoring_data or not self.monitoring_data[key]["active"]:
            # Return current history if available
            if key in self.value_history and self.value_history[key]["values"]:
                history_df = self._create_history_dataframe(self.value_history[key]["values"])
                latest = self.value_history[key]["values"][-1]
                
                # Analyze latest value
                analysis = self._analyze_value(latest["raw_value"], min_pattern_len, max_pattern_len)
                
                return (
                    self._format_hex_display(latest["raw_value"]),
                    self._create_value_info(latest["raw_value"]),
                    self._create_pattern_summary(analysis["patterns"]),
                    analysis["patterns"].patterns if analysis["patterns"] else [],
                    self._create_pattern_visualization(latest["raw_value"], analysis["patterns"]),
                    history_df,
                    analysis["sequences"],
                    analysis["encodings"],
                    analysis["bit_patterns"]
                )
            
            return ("No data", {}, "**Pattern Analysis**\n\nNo active monitoring",
                   [], "", [], {}, {}, [])
        
        # Check if it's time to read
        now = datetime.now()
        last_read = self.monitoring_data[key]["last_read"]
        interval = self.monitoring_data[key]["interval"]
        
        if last_read is None or (now - last_read).total_seconds() >= interval:
            # Read the characteristic
            try:
                result = self.client.read_characteristic(address, char_uuid)
                
                if "error" not in result:
                    raw_value = result.get("value", b"")
                    if isinstance(raw_value, str):
                        raw_value = bytes.fromhex(raw_value)
                    
                    # Update history
                    self._add_to_history(key, raw_value)
                    self.monitoring_data[key]["last_read"] = now
                    
                    # Analyze value
                    analysis = self._analyze_value(raw_value, min_pattern_len, max_pattern_len)
                    
                    # Create history dataframe
                    history_df = self._create_history_dataframe(self.value_history[key]["values"])
                    
                    return (
                        self._format_hex_display(raw_value),
                        self._create_value_info(raw_value),
                        self._create_pattern_summary(analysis["patterns"]),
                        analysis["patterns"].patterns if analysis["patterns"] else [],
                        self._create_pattern_visualization(raw_value, analysis["patterns"]),
                        history_df,
                        analysis["sequences"],
                        analysis["encodings"],
                        analysis["bit_patterns"]
                    )
            except:
                pass
        
        # Return current state
        if key in self.value_history and self.value_history[key]["values"]:
            history_df = self._create_history_dataframe(self.value_history[key]["values"])
            latest = self.value_history[key]["values"][-1]
            analysis = self._analyze_value(latest["raw_value"], min_pattern_len, max_pattern_len)
            
            return (
                self._format_hex_display(latest["raw_value"]),
                self._create_value_info(latest["raw_value"]),
                self._create_pattern_summary(analysis["patterns"]),
                analysis["patterns"].patterns if analysis["patterns"] else [],
                self._create_pattern_visualization(latest["raw_value"], analysis["patterns"]),
                history_df,
                analysis["sequences"],
                analysis["encodings"],
                analysis["bit_patterns"]
            )
        
        return ("No data", {}, "**Pattern Analysis**\n\nWaiting for data...",
               [], "", [], {}, {}, [])
    
    def _analyze_value(self, data: bytes, min_pattern_len: int, max_pattern_len: int) -> Dict[str, Any]:
        """Analyze a characteristic value"""
        # Update pattern matcher settings
        self.pattern_matcher.min_pattern_length = min_pattern_len
        self.pattern_matcher.max_pattern_length = max_pattern_len
        
        # Run pattern analysis
        patterns = self.pattern_matcher.analyze(data)
        
        # Find sequences
        sequences = self.pattern_matcher.find_sequences(data)
        
        # Detect encoding
        encodings = self.pattern_matcher.detect_encoding(data)
        
        # Find bit patterns
        bit_patterns = self.pattern_matcher.find_bit_patterns(data)
        
        return {
            "patterns": patterns,
            "sequences": sequences,
            "encodings": encodings,
            "bit_patterns": bit_patterns[:10]  # Limit to top 10
        }
    
    def _format_hex_display(self, data: bytes) -> str:
        """Format hex data for display"""
        if not data:
            return "No data"
        
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = ' '.join(f"{b:02x}" for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{i:04x}: {hex_part:<48} {ascii_part}")
        
        return '\n'.join(lines)
    
    def _create_value_info(self, data: bytes) -> Dict[str, Any]:
        """Create value information summary"""
        if not data:
            return {"error": "No data"}
        
        return {
            "length": len(data),
            "hex": data.hex(),
            "first_4_bytes": data[:4].hex() if len(data) >= 4 else data.hex(),
            "last_4_bytes": data[-4:].hex() if len(data) >= 4 else data.hex(),
            "checksum": hex(sum(data) & 0xFF),
            "unique_bytes": len(set(data)),
            "all_printable": all(32 <= b < 127 for b in data)
        }
    
    def _create_pattern_summary(self, pattern_match: Optional[PatternMatch]) -> str:
        """Create pattern analysis summary"""
        if not pattern_match or not pattern_match.patterns:
            return "**Pattern Analysis**\n\nNo repeating patterns detected"
        
        summary = f"""**Pattern Analysis**

📊 **Summary**
- **Patterns Found:** {len(pattern_match.patterns)}
- **Data Coverage:** {pattern_match.coverage:.1%}
- **Entropy:** {pattern_match.entropy:.2f} (0=uniform, 1=random)

🔝 **Top Patterns**
"""
        
        for i, pattern in enumerate(pattern_match.patterns[:5]):
            summary += f"\n{i+1}. `{pattern.hex_pattern}` - {pattern.count} times, length {pattern.length}"
        
        if pattern_match.most_frequent:
            summary += f"\n\n**Most Frequent:** `{pattern_match.most_frequent.hex_pattern}` ({pattern_match.most_frequent.count} occurrences)"
        
        return summary
    
    def _create_pattern_visualization(self, data: bytes, pattern_match: Optional[PatternMatch]) -> str:
        """Create visual representation of patterns"""
        if not data or not pattern_match or not pattern_match.patterns:
            return ""
        
        # Create a map of positions to patterns
        position_map = {}
        for i, pattern in enumerate(pattern_match.patterns[:5]):  # Top 5 patterns
            for pos in pattern.positions:
                for j in range(pattern.length):
                    if pos + j < len(data):
                        position_map[pos + j] = i + 1
        
        # Build visualization
        viz = []
        hex_line = []
        pattern_line = []
        
        for i, byte in enumerate(data):
            hex_line.append(f"{byte:02x}")
            if i in position_map:
                pattern_line.append(f"[{position_map[i]}]")
            else:
                pattern_line.append("   ")
            
            if (i + 1) % 16 == 0 or i == len(data) - 1:
                viz.append(' '.join(hex_line))
                viz.append(' '.join(pattern_line))
                viz.append("")
                hex_line = []
                pattern_line = []
        
        viz.append("\nPattern Legend:")
        for i, pattern in enumerate(pattern_match.patterns[:5]):
            viz.append(f"[{i+1}] = {pattern.hex_pattern}")
        
        return '\n'.join(viz)
    
    def _add_to_history(self, key: str, value: bytes):
        """Add value to history"""
        if key not in self.value_history:
            self.value_history[key] = {"values": [], "limit": 100}
        
        history = self.value_history[key]
        
        # Calculate change from previous
        change = ""
        if history["values"]:
            prev_value = history["values"][-1]["raw_value"]
            if value != prev_value:
                if len(value) != len(prev_value):
                    change = f"Length: {len(prev_value)} → {len(value)}"
                else:
                    # Find first different byte
                    for i, (a, b) in enumerate(zip(prev_value, value)):
                        if a != b:
                            change = f"Byte {i}: {a:02x} → {b:02x}"
                            break
        
        # Add to history
        history["values"].append({
            "timestamp": datetime.now(),
            "raw_value": value,
            "change": change
        })
        
        # Trim history
        if len(history["values"]) > history["limit"]:
            history["values"] = history["values"][-history["limit"]:]
    
    def _create_history_dataframe(self, history: List[Dict]) -> List[List]:
        """Create dataframe data from history"""
        rows = []
        
        for entry in history[-20:]:  # Last 20 entries
            timestamp = entry["timestamp"].strftime("%H:%M:%S.%f")[:-3]
            raw_value = entry["raw_value"]
            hex_value = raw_value.hex() if len(raw_value) <= 8 else raw_value[:8].hex() + "..."
            ascii_value = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_value[:8])
            length = len(raw_value)
            change = entry.get("change", "")
            
            rows.append([timestamp, hex_value, ascii_value, length, change])
        
        return rows