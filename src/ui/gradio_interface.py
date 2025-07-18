#!/usr/bin/env python3
"""
BlueFusion Gradio Interface - Fixed Version
Interactive web UI for BLE scanning and monitoring
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gradio as gr
from typing import Tuple, Any
from datetime import datetime

# Import modular components
try:
    # Try relative imports first (when used as a module)
    from .client import BlueFusionClient
    from .websocket_handler import WebSocketHandler
    from .interface_handlers import InterfaceHandlers
    from .visualization import Visualizer
    from .data_processing import DataProcessor
    from .data_models import API_BASE, WS_URL, ScanConfig
    from .wiki import WikiHandler
    from .packet_inspector_ui import PacketInspectorUI
    from .roadmap.roadmap_ui_simple import SimplifiedRoadmapUI
    from .service_explorer_ui import ServiceExplorerUI
except ImportError:
    # Fall back to absolute imports (when run directly)
    from client import BlueFusionClient
    from websocket_handler import WebSocketHandler
    from interface_handlers import InterfaceHandlers
    from visualization import Visualizer
    from data_processing import DataProcessor
    from data_models import API_BASE, WS_URL, ScanConfig
    from wiki import WikiHandler
    from packet_inspector_ui import PacketInspectorUI
    from roadmap.roadmap_ui_simple import SimplifiedRoadmapUI
    from service_explorer_ui import ServiceExplorerUI


# Create a function to get fresh client instances
def get_client():
    """Get a fresh client instance"""
    return BlueFusionClient(API_BASE)


# Initialize components with lazy loading
visualizer = Visualizer()
data_processor = DataProcessor()
wiki_handler = WikiHandler()
packet_inspector_ui = PacketInspectorUI()
roadmap_ui = SimplifiedRoadmapUI()

# These will be initialized on first use
_client = None
_ws_handler = None
_interface_handlers = None
_service_explorer_ui = None


def ensure_initialized():
    """Ensure all components are initialized"""
    global _client, _ws_handler, _interface_handlers, _service_explorer_ui
    
    if _client is None:
        print("Initializing BlueFusion client...")
        _client = BlueFusionClient(API_BASE)
    
    if _ws_handler is None:
        print("Initializing WebSocket handler...")
        _ws_handler = WebSocketHandler(WS_URL)
    
    if _interface_handlers is None:
        print("Initializing interface handlers...")
        _interface_handlers = InterfaceHandlers(_client, _ws_handler)
    
    if _service_explorer_ui is None:
        print("Initializing service explorer...")
        _service_explorer_ui = ServiceExplorerUI(_client)
    
    return _client, _ws_handler, _interface_handlers, _service_explorer_ui


def start_scanning(interface: str, mode: str) -> Tuple[str, str]:
    """Start BLE scanning"""
    print(f"DEBUG: start_scanning called with interface={interface}, mode={mode}")
    try:
        client, ws_handler, interface_handlers, _ = ensure_initialized()
        result = interface_handlers.start_scanning(interface, mode)
        print(f"DEBUG: start_scanning result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: start_scanning error: {e}")
        import traceback
        traceback.print_exc()
        # Try to reinitialize on error
        global _client, _interface_handlers
        _client = None
        _interface_handlers = None
        return f"❌ Error: {str(e)}", "Connection error - try refreshing the page"


def stop_scanning(interface: str) -> Tuple[str, str]:
    """Stop BLE scanning"""
    try:
        _, _, interface_handlers, _ = ensure_initialized()
        return interface_handlers.stop_scanning(interface)
    except Exception as e:
        return f"❌ Error: {str(e)}", "Connection error"


def get_interface_status() -> str:
    """Get current status of interfaces"""
    try:
        _, _, interface_handlers, _ = ensure_initialized()
        return interface_handlers.get_interface_status()
    except Exception as e:
        return f"❌ Connection Error: {str(e)}\n\nCannot connect to API server at {API_BASE}"


def get_device_list(interface: str):
    """Get discovered devices as DataFrame"""
    try:
        client, _, _, _ = ensure_initialized()
        devices = client.get_devices(ScanConfig.normalize_interface(interface))
        return data_processor.format_device_list(devices)
    except Exception as e:
        print(f"Error getting device list: {e}")
        return None


def get_packet_stream():
    """Get recent packets from queue"""
    try:
        _, ws_handler, _, _ = ensure_initialized()
        packets = ws_handler.get_packets(50)
        return data_processor.format_packet_stream(packets)
    except Exception as e:
        print(f"Error getting packet stream: {e}")
        return None


def create_rssi_plot():
    """Create RSSI plot for top devices"""
    try:
        _, ws_handler, _, _ = ensure_initialized()
        return visualizer.create_rssi_plot(ws_handler.device_data)
    except Exception as e:
        print(f"Error creating RSSI plot: {e}")
        return None


def create_activity_plot():
    """Create activity timeline plot"""
    try:
        _, ws_handler, _, _ = ensure_initialized()
        return visualizer.create_activity_plot(ws_handler.packet_history)
    except Exception as e:
        print(f"Error creating activity plot: {e}")
        return None


def set_channel(channel: int) -> str:
    """Set sniffer channel"""
    try:
        _, _, interface_handlers, _ = ensure_initialized()
        return interface_handlers.set_channel(channel)
    except Exception as e:
        return f"❌ Error: {str(e)}"


def update_live_data():
    """Update live monitoring data"""
    return get_packet_stream(), create_rssi_plot(), create_activity_plot()


def update_stats():
    """Update statistics"""
    try:
        _, _, interface_handlers, _ = ensure_initialized()
        return interface_handlers.format_statistics()
    except Exception as e:
        return f"Error: {str(e)}"


def load_wiki_content(topic: str) -> str:
    """Load wiki content based on selected topic"""
    return wiki_handler.get_content(topic)


def search_wiki(query: str) -> str:
    """Search wiki content"""
    if not query.strip():
        return "Enter a search term to search the wiki."
    return wiki_handler.search_content(query)


def get_recent_packets_for_selector():
    """Get recent packets formatted for dropdown selector"""
    try:
        _, ws_handler, _, _ = ensure_initialized()
        packets = ws_handler.get_recent_packets(20)
        choices = []
        
        if not packets:
            return [("No packets available - Start scanning first", None)]
        
        for i, packet in enumerate(packets):
            if isinstance(packet, dict):
                timestamp = packet.get('timestamp', '')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
                else:
                    timestamp = timestamp.strftime("%H:%M:%S")
                address = packet.get('address', 'Unknown')
                packet_type = packet.get('packet_type', 'Unknown')
            else:
                timestamp = packet.timestamp.strftime("%H:%M:%S")
                address = packet.address
                packet_type = packet.packet_type
                
            label = f"{timestamp} | {address[:8]}... | {packet_type}"
            choices.append((label, i))
        return choices
    except Exception as e:
        print(f"Error getting packets for selector: {e}")
        return [("Error loading packets", None)]


def inspect_selected_packet(packet_index: int):
    """Inspect a selected packet"""
    if packet_index is None:
        return """No packet selected. 

**To use the Packet Inspector:**
1. Go to the **Control** tab
2. Select an interface (Both, MacBook, or Sniffer)
3. Click **Start Scan** to begin capturing packets
4. Return to this tab and select a packet from the dropdown
5. Click **Inspect Packet** to analyze it

The packet inspector will show:
- Protocol analysis (GATT/ATT, L2CAP, etc.)
- Parsed fields and values
- Security indicators
- Hex dump of packet data""", None, None
    
    try:
        _, ws_handler, _, _ = ensure_initialized()
        packets = ws_handler.get_recent_packets(20)
        if 0 <= packet_index < len(packets):
            packet = packets[packet_index]
            
            if isinstance(packet, dict):
                packet_data = {
                    "timestamp": packet.get('timestamp', datetime.now().isoformat()),
                    "source": packet.get('source', 'unknown'),
                    "address": packet.get('address', ''),
                    "rssi": packet.get('rssi', -65),
                    "data": packet.get('data', ''),
                    "packet_type": packet.get('packet_type', 'data'),
                    "metadata": packet.get('metadata', {})
                }
            else:
                packet_data = {
                    "timestamp": getattr(packet, 'timestamp', datetime.now().isoformat()),
                    "source": getattr(packet, 'source', 'unknown'),
                    "address": getattr(packet, 'address', ''),
                    "rssi": getattr(packet, 'rssi', -65),
                    "data": getattr(packet, 'data', ''),
                    "packet_type": getattr(packet, 'packet_type', 'data'),
                    "metadata": getattr(packet, 'metadata', {})
                }
            
            result = packet_inspector_ui.inspect_packet(packet_data)
            summary = packet_inspector_ui.get_inspection_summary(result)
            fields_df = packet_inspector_ui.format_parsed_fields(result)
            hex_display = packet_inspector_ui.get_hex_dump_display(result)
            
            return summary, fields_df, hex_display
        
        return "Invalid packet selection", None, None
        
    except Exception as e:
        import traceback
        error_msg = f"**Error in packet inspection:**\n\n{str(e)}\n\n**Traceback:**\n```\n{traceback.format_exc()}\n```"
        return error_msg, None, None


def get_inspector_statistics():
    """Get packet inspector statistics"""
    protocol_df = packet_inspector_ui.get_statistics_display()
    security_df = packet_inspector_ui.get_security_statistics()
    return protocol_df, security_df


# Create Gradio interface
with gr.Blocks(title="BlueFusion BLE Monitor", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🔵 BlueFusion BLE Monitor")
    gr.Markdown("Dual interface BLE monitoring with MacBook native BLE and USB sniffer dongle")
    
    with gr.Tab("Control"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Interface Control")
                interface_select = gr.Radio(
                    ScanConfig.INTERFACES,
                    value=ScanConfig.DEFAULT_INTERFACE,
                    label="Interface"
                )
                mode_select = gr.Radio(
                    ScanConfig.MODES,
                    value=ScanConfig.DEFAULT_MODE,
                    label="Scan Mode"
                )
                
                with gr.Row():
                    start_btn = gr.Button("Start Scan", variant="primary")
                    stop_btn = gr.Button("Stop Scan", variant="stop")
                
                scan_output = gr.Textbox(
                    label="Scan Status",
                    lines=2,
                    interactive=False
                )
            
            with gr.Column(scale=2):
                gr.Markdown("### Interface Status")
                status_display = gr.Textbox(
                    label="Current Status",
                    lines=10,
                    interactive=False
                )
                refresh_btn = gr.Button("Refresh Status")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Sniffer Settings")
                channel_slider = gr.Slider(
                    minimum=0,
                    maximum=39,
                    value=ScanConfig.DEFAULT_CHANNEL,
                    step=1,
                    label="BLE Channel"
                )
                set_channel_btn = gr.Button("Set Channel")
                channel_output = gr.Textbox(label="Channel Status", interactive=False)
    
    with gr.Tab("Devices"):
        gr.Markdown("### Discovered Devices")
        
        with gr.Row():
            device_interface = gr.Radio(
                ScanConfig.INTERFACES,
                value=ScanConfig.DEFAULT_INTERFACE,
                label="Show devices from"
            )
            refresh_devices_btn = gr.Button("Refresh Devices")
        
        device_table = gr.DataFrame(
            label="Device List",
            interactive=True,
            wrap=True
        )
    
    with gr.Tab("Live Monitor"):
        gr.Markdown("### Real-time Packet Stream")
        
        packet_table = gr.DataFrame(
            label="Recent Packets",
            interactive=True,
            wrap=True
        )
        
        with gr.Row():
            rssi_plot = gr.Plot(label="RSSI Levels")
            activity_plot = gr.Plot(label="Activity Timeline")
        
        # Auto-refresh for live data
        refresh_interval = gr.Slider(
            minimum=1,
            maximum=10,
            value=2,
            step=1,
            label="Refresh Interval (seconds)"
        )
    
    with gr.Tab("Statistics"):
        gr.Markdown("### Packet Statistics")
        
        stats_text = gr.Textbox(
            label="Summary Statistics",
            lines=15,
            interactive=True
        )
        
        refresh_stats_btn = gr.Button("Refresh Statistics")
    
    with gr.Tab("Service Explorer"):
        gr.Markdown("### 🔍 GATT Service Explorer")
        gr.Markdown("Explore BLE device services, characteristics, and descriptors")
        
        # Initialize and create Service Explorer interface
        _, _, _, service_explorer_ui = ensure_initialized()
        if service_explorer_ui:
            # Create the interface and capture returned components
            service_explorer_components = service_explorer_ui.create_interface()
        else:
            gr.Markdown("⚠️ Service Explorer initialization failed. Please refresh the page.")
    
    with gr.Tab("Packet Inspector"):
        gr.Markdown("### 🔍 Deep Packet Analysis")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### Select Packet")
                packet_selector = gr.Dropdown(
                    label="Recent Packets",
                    choices=[],
                    value=None,
                    interactive=True
                )
                inspect_btn = gr.Button("Inspect Packet", variant="primary")
                
                gr.Markdown("#### Inspector Statistics")
                protocol_stats = gr.Dataframe(
                    label="Protocol Distribution",
                    interactive=True
                )
                
                security_stats = gr.Dataframe(
                    label="Security Events",
                    interactive=True
                )
            
            with gr.Column(scale=2):
                gr.Markdown("#### Inspection Results")
                inspection_summary = gr.Textbox(
                    label="Analysis Summary",
                    lines=15,
                    interactive=False
                )
                
                with gr.Row():
                    with gr.Column():
                        parsed_fields = gr.Dataframe(
                            label="Parsed Fields",
                            interactive=True
                        )
                    with gr.Column():
                        hex_dump = gr.Textbox(
                            label="Hex Dump",
                            lines=10,
                            interactive=True
                        )
    
    with gr.Tab("Wiki"):
        gr.Markdown("### 📚 BlueFusion Wiki")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### Navigation")
                wiki_topics = gr.Radio(
                    choices=wiki_handler.get_topics(),
                    value="Getting Started",
                    label="Wiki Topics"
                )
                
                gr.Markdown("#### Search")
                search_input = gr.Textbox(
                    label="Search Wiki",
                    placeholder="Enter search terms...",
                    lines=1
                )
                search_btn = gr.Button("Search")
                
            with gr.Column(scale=3):
                wiki_content = gr.Markdown(
                    value=wiki_handler.get_content("Getting Started"),
                    label="Documentation"
                )
    
    with gr.Tab("Roadmap"):
        gr.Markdown("# 🚀 BlueFusion Feature Roadmap")
        
        with gr.Row():
            with gr.Column(scale=1):
                stats_display = gr.Markdown(value=roadmap_ui.get_quick_stats())
                
                gr.Markdown("### 🔍 Quick Search")
                roadmap_search_input = gr.Textbox(
                    placeholder="Type to search features...",
                    label="Search"
                )
                search_results = gr.Dataframe(
                    headers=["Feature", "Category", "Description"],
                    interactive=False,
                    visible=False
                )
            
            with gr.Column(scale=2):
                gr.Markdown("### 📁 Select Category")
                category_select = gr.Dropdown(
                    choices=roadmap_ui.get_categories_with_counts(),
                    value=roadmap_ui.get_categories_with_counts()[0],
                    label="Category"
                )
                
                features_table = gr.Dataframe(
                    headers=["#", "Feature", "Description", "Status"],
                    label="Click a feature to select it",
                    interactive=False
                )
                
                with gr.Row():
                    with gr.Column():
                        selected_status = gr.Textbox(
                            label="Selected Feature",
                            value="No feature selected",
                            interactive=False
                        )
                        
                        with gr.Row():
                            status_radio = gr.Radio(
                                choices=["pending", "partial", "completed"],
                                value="pending",
                                label="Update Status"
                            )
                            update_btn = gr.Button("Update", size="sm")
                        
                        notes_input = gr.Textbox(
                            placeholder="Add notes...",
                            label="Notes",
                            lines=2
                        )
                    
                    with gr.Column():
                        feature_context = gr.Textbox(
                            label="Feature Details",
                            lines=5,
                            interactive=False
                        )
                        
                        copy_text = gr.Textbox(
                            label="📋 Copy this to Claude Code:",
                            lines=3,
                            interactive=True
                        )
        
        with gr.Row():
            gr.Markdown("### 🚀 Quick Actions")
            with gr.Column():
                batch_context_btn = gr.Button("Get all pending features in category", variant="secondary")
                batch_output = gr.Textbox(
                    label="Batch Context",
                    lines=10,
                    interactive=True,
                    visible=False
                )
    
    # Event handlers
    start_btn.click(
        start_scanning,
        inputs=[interface_select, mode_select],
        outputs=[scan_output, status_display]
    )
    
    stop_btn.click(
        stop_scanning,
        inputs=[interface_select],
        outputs=[scan_output, status_display]
    )
    
    refresh_btn.click(
        get_interface_status,
        outputs=[status_display]
    )
    
    refresh_devices_btn.click(
        get_device_list,
        inputs=[device_interface],
        outputs=[device_table]
    )
    
    set_channel_btn.click(
        set_channel,
        inputs=[channel_slider],
        outputs=[channel_output]
    )
    
    refresh_stats_btn.click(
        update_stats,
        outputs=[stats_text]
    )
    
    # Wiki event handlers
    wiki_topics.change(
        load_wiki_content,
        inputs=[wiki_topics],
        outputs=[wiki_content]
    )
    
    search_btn.click(
        search_wiki,
        inputs=[search_input],
        outputs=[wiki_content]
    )
    
    search_input.submit(
        search_wiki,
        inputs=[search_input],
        outputs=[wiki_content]
    )
    
    # Roadmap handlers
    def on_category_change(category):
        features = roadmap_ui.format_feature_list(category)
        return features
    
    def on_feature_select(category, evt: gr.SelectData):
        if evt.index is not None:
            selected_rows = [evt.index[0]]
            status, context, copy = roadmap_ui.select_feature(category, selected_rows)
            return status, context, copy
        return "No selection", "", ""
    
    def update_feature_status(status, notes):
        result, updated_table = roadmap_ui.update_feature_status(status, notes)
        return result, updated_table, roadmap_ui.get_quick_stats()
    
    def search_features(query):
        if query.strip():
            results = roadmap_ui.search_all_features(query)
            return gr.Dataframe(value=results, visible=True)
        return gr.Dataframe(visible=False)
    
    def generate_batch_context(category):
        context = roadmap_ui.generate_batch_context(category)
        return gr.Textbox(value=context, visible=True)
    
    category_select.change(
        on_category_change,
        inputs=[category_select],
        outputs=[features_table]
    )
    
    features_table.select(
        on_feature_select,
        inputs=[category_select],
        outputs=[selected_status, feature_context, copy_text]
    )
    
    update_btn.click(
        update_feature_status,
        inputs=[status_radio, notes_input],
        outputs=[selected_status, features_table, stats_display]
    )
    
    roadmap_search_input.change(
        search_features,
        inputs=[roadmap_search_input],
        outputs=[search_results]
    )
    
    batch_context_btn.click(
        generate_batch_context,
        inputs=[category_select],
        outputs=[batch_output]
    )
    
    # Load initial data
    app.load(
        lambda: (
            roadmap_ui.format_feature_list(roadmap_ui.get_categories_with_counts()[0]),
            roadmap_ui.get_quick_stats()
        ),
        outputs=[features_table, stats_display]
    )
    
    # Packet Inspector handlers
    def update_packet_selector():
        choices = get_recent_packets_for_selector()
        if choices and choices[0][1] is None:
            return gr.Dropdown(choices=choices, value=None)
        return gr.Dropdown(choices=choices, value=None if not choices else choices[0][1])
    
    inspect_btn.click(
        inspect_selected_packet,
        inputs=[packet_selector],
        outputs=[inspection_summary, parsed_fields, hex_dump]
    )
    
    # Auto-refresh packet selector
    packet_selector_timer = gr.Timer(value=3)
    packet_selector_timer.tick(
        update_packet_selector,
        outputs=[packet_selector]
    )
    
    # Auto-refresh inspector statistics
    stats_timer = gr.Timer(value=5)
    stats_timer.tick(
        get_inspector_statistics,
        outputs=[protocol_stats, security_stats]
    )
    
    # Auto-refresh timer for live data
    timer = gr.Timer(value=2)
    timer.tick(
        update_live_data,
        outputs=[packet_table, rssi_plot, activity_plot]
    )
    
    # Load initial status with error handling
    def safe_get_interface_status():
        try:
            return get_interface_status()
        except Exception as e:
            return f"❌ Error loading status: {str(e)}\n\nPlease check API connection"
    
    app.load(
        safe_get_interface_status,
        outputs=[status_display]
    )
    
    # Load initial packet inspector state
    app.load(
        lambda: (
            update_packet_selector(),
            inspect_selected_packet(None)[0],
            *get_inspector_statistics()
        ),
        outputs=[packet_selector, inspection_summary, protocol_stats, security_stats]
    )


if __name__ == "__main__":
    print("Starting BlueFusion Gradio Interface (Fixed)...")
    print(f"API endpoint: {API_BASE}")
    print(f"WebSocket endpoint: {WS_URL}")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    
    # Test initial connection
    try:
        test_client = BlueFusionClient(API_BASE)
        status = test_client.get_status()
        print(f"✅ API connection successful: {status}")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to API at startup: {e}")
        print("   The UI will attempt to connect when you interact with it.")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )