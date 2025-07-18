#!/usr/bin/env python3
"""
Service Explorer UI Component
Interactive interface for exploring BLE device services, characteristics, and descriptors
"""
import gradio as gr
from typing import Dict, Any, List, Optional, Tuple
import json

class ServiceExplorerUI:
    """Service Explorer UI component for BLE GATT exploration"""
    
    def __init__(self, client):
        self.client = client
        self.connected_devices = {}
        self.service_data = {}
        
    def create_interface(self):
        """Create the Service Explorer UI interface"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Device Selection")
                
                # Device selector from scanned devices
                device_selector = gr.Dropdown(
                    label="Select Discovered Device",
                    choices=[],
                    interactive=True,
                    info="Choose from devices found in scanning"
                )
                
                with gr.Row():
                    refresh_devices_btn = gr.Button("🔄 Refresh Device List", variant="secondary")
                    copy_address_btn = gr.Button("📋 Copy Address", variant="secondary")
                
                # Selected device info
                selected_device_info = gr.Markdown("**Selected Device:** None")
                
                gr.Markdown("**OR**")
                
                # Manual device address entry
                device_address = gr.Textbox(
                    label="Manual Device Address",
                    placeholder="Enter BLE device address (e.g., AA:BB:CC:DD:EE:FF)",
                    info="Manually enter device address"
                )
                
                gr.Markdown("### Device Connection")
                with gr.Row():
                    connect_btn = gr.Button("Connect", variant="primary")
                    disconnect_btn = gr.Button("Disconnect", variant="secondary")
                
                connection_status = gr.Markdown("**Status:** Not connected")
                
                gr.Markdown("### Service Discovery")
                discover_btn = gr.Button("Discover All Services", variant="primary")
                discovery_status = gr.Markdown("**Discovery Status:** Ready")
                
            with gr.Column(scale=2):
                gr.Markdown("### Service Explorer")
                
                with gr.Tabs():
                    with gr.Tab("Service Tree"):
                        service_tree = gr.JSON(
                            label="Services, Characteristics & Descriptors",
                            value={"message": "Connect to a device and discover services to see the GATT structure"}
                        )
                        
                    with gr.Tab("Service Details"):
                        service_dropdown = gr.Dropdown(
                            label="Select Service",
                            choices=[],
                            interactive=True
                        )
                        service_info = gr.JSON(
                            label="Service Information",
                            value={}
                        )
                        
                        char_dropdown = gr.Dropdown(
                            label="Select Characteristic",
                            choices=[],
                            interactive=True
                        )
                        char_info = gr.JSON(
                            label="Characteristic Information", 
                            value={}
                        )
                        
                        desc_dropdown = gr.Dropdown(
                            label="Select Descriptor",
                            choices=[],
                            interactive=True
                        )
                        desc_info = gr.JSON(
                            label="Descriptor Information",
                            value={}
                        )
                        
                    with gr.Tab("Raw Data"):
                        raw_data = gr.Code(
                            label="Raw Discovery Data",
                            language="json",
                            value="{}"
                        )
                        
                    with gr.Tab("Statistics"):
                        stats_display = gr.Markdown("**Discovery Statistics**\n\nNo data available")
        
        # Event handlers
        refresh_devices_btn.click(
            self.refresh_device_list,
            outputs=[device_selector]
        )
        
        
        connect_btn.click(
            self.connect_device_unified,
            inputs=[device_selector, device_address],
            outputs=[connection_status]
        )
        
        disconnect_btn.click(
            self.disconnect_device_unified,
            inputs=[device_selector, device_address],
            outputs=[connection_status, service_tree, service_dropdown, char_dropdown, desc_dropdown, raw_data, stats_display]
        )
        
        discover_btn.click(
            self.discover_all_services_unified,
            inputs=[device_selector, device_address],
            outputs=[discovery_status, service_tree, service_dropdown, raw_data, stats_display]
        )
        
        service_dropdown.change(
            self.on_service_selected_unified,
            inputs=[device_selector, device_address, service_dropdown],
            outputs=[service_info, char_dropdown]
        )
        
        char_dropdown.change(
            self.on_characteristic_selected_unified,
            inputs=[device_selector, device_address, char_dropdown],
            outputs=[char_info, desc_dropdown]
        )
        
        desc_dropdown.change(
            self.on_descriptor_selected_unified,
            inputs=[device_selector, device_address, desc_dropdown],
            outputs=[desc_info]
        )
        
        # Add copy address functionality
        copy_address_btn.click(
            self.copy_device_address,
            inputs=[device_selector, device_address],
            outputs=[selected_device_info]
        )
        
        # Update device selector to show selected device info
        device_selector.change(
            self.on_device_selected,
            inputs=[device_selector],
            outputs=[device_address, selected_device_info]
        )
        
        return [
            device_selector, refresh_devices_btn, copy_address_btn, selected_device_info,
            device_address, connect_btn, disconnect_btn, connection_status,
            discover_btn, discovery_status, service_tree, service_dropdown,
            service_info, char_dropdown, char_info, desc_dropdown, desc_info,
            raw_data, stats_display
        ]
    
    def refresh_device_list(self) -> gr.Dropdown:
        """Refresh the list of discovered devices"""
        try:
            # Get devices from both interfaces
            devices_data = self.client.get_devices("both")
            
            device_choices = []
            
            # Process MacBook BLE devices
            if "macbook" in devices_data and devices_data["macbook"]:
                for device in devices_data["macbook"]:
                    address = device.get("address", "")
                    name = device.get("name", "Unknown")
                    rssi = device.get("rssi", 0)
                    
                    if address:
                        display_name = f"{address} | {name} | {rssi} dBm"
                        device_choices.append((display_name, address))
            
            # Process Sniffer devices
            if "sniffer" in devices_data and devices_data["sniffer"]:
                for device in devices_data["sniffer"]:
                    address = device.get("address", "")
                    name = device.get("name", "Unknown")
                    rssi = device.get("rssi", 0)
                    
                    if address:
                        display_name = f"{address} | {name} | {rssi} dBm (Sniffer)"
                        # Check if device is already in choices to avoid duplicates
                        if not any(choice[1] == address for choice in device_choices):
                            device_choices.append((display_name, address))
            
            # Sort by RSSI (signal strength) - stronger signals first
            def get_rssi(choice):
                try:
                    rssi_str = choice[0].split('|')[2].strip().split()[0]
                    return int(rssi_str)
                except (IndexError, ValueError):
                    return -100  # Default low RSSI for unparseable values
            
            device_choices.sort(key=get_rssi, reverse=True)
            
            return gr.Dropdown(choices=device_choices)
        
        except Exception as e:
            print(f"Error refreshing device list: {e}")
            return gr.Dropdown(choices=[])
    
    def on_device_selected(self, selected_device: str) -> Tuple[str, str]:
        """Handle device selection from dropdown"""
        if selected_device:
            # The selected_device is already the address (value from dropdown)
            device_info = f"**Selected Device:** `{selected_device}`"
            return selected_device, device_info
        return "", "**Selected Device:** None"
    
    def copy_device_address(self, selected_device: str, manual_address: str) -> str:
        """Copy device address to clipboard (simulation)"""
        # Use selected device if available, otherwise use manual address
        address = selected_device if selected_device else manual_address
        
        if address:
            # In a real implementation, this would copy to system clipboard
            # For now, we'll just show a message and note the address
            return f"**📋 Address copied:** `{address}`\n\n*Note: In a real implementation, this would copy to your system clipboard*"
        return "**❌ No address to copy**"
    
    def connect_device_unified(self, selected_device: str, manual_address: str) -> str:
        """Connect to a device using either selected or manual address"""
        # Use selected device if available, otherwise use manual address
        address = selected_device if selected_device else manual_address
        return self.connect_device(address)
    
    def disconnect_device_unified(self, selected_device: str, manual_address: str) -> Tuple[str, Dict, gr.Dropdown, gr.Dropdown, gr.Dropdown, str, str]:
        """Disconnect from a device using either selected or manual address"""
        # Use selected device if available, otherwise use manual address
        address = selected_device if selected_device else manual_address
        return self.disconnect_device(address)
    
    def discover_all_services_unified(self, selected_device: str, manual_address: str) -> Tuple[str, Dict, gr.Dropdown, str, str]:
        """Discover services for a device using either selected or manual address"""
        # Use selected device if available, otherwise use manual address
        address = selected_device if selected_device else manual_address
        return self.discover_all_services(address)
    
    def connect_device(self, address: str) -> str:
        """Connect to a BLE device"""
        if not address:
            return "**Status:** ❌ Please enter a device address"
        
        result = self.client.connect_device(address)
        
        if "error" in result:
            return f"**Status:** ❌ Connection failed: {result['error']}"
        
        if result.get("status") == "connected":
            self.connected_devices[address] = True
            return f"**Status:** ✅ Connected to {address}"
        else:
            return f"**Status:** ❌ Connection failed"
    
    def disconnect_device(self, address: str) -> Tuple[str, Dict, gr.Dropdown, gr.Dropdown, gr.Dropdown, str, str]:
        """Disconnect from a BLE device"""
        if not address:
            return "**Status:** ❌ Please enter a device address", {}, gr.Dropdown(choices=[]), gr.Dropdown(choices=[]), gr.Dropdown(choices=[]), "{}", "**Discovery Statistics**\n\nNo data available"
        
        result = self.client.disconnect_device(address)
        
        if address in self.connected_devices:
            del self.connected_devices[address]
        if address in self.service_data:
            del self.service_data[address]
        
        status = f"**Status:** ✅ Disconnected from {address}"
        empty_tree = {"message": "Connect to a device and discover services to see the GATT structure"}
        empty_dropdown = gr.Dropdown(choices=[])
        empty_stats = "**Discovery Statistics**\n\nNo data available"
        
        return status, empty_tree, empty_dropdown, empty_dropdown, empty_dropdown, "{}", empty_stats
    
    def discover_all_services(self, address: str) -> Tuple[str, Dict, gr.Dropdown, str, str]:
        """Discover all services for a connected device"""
        if not address:
            return "**Discovery Status:** ❌ Please enter a device address", {}, gr.Dropdown(choices=[]), "{}", "**Discovery Statistics**\n\nNo data available"
        
        if address not in self.connected_devices:
            return "**Discovery Status:** ❌ Device not connected", {}, gr.Dropdown(choices=[]), "{}", "**Discovery Statistics**\n\nNo data available"
        
        # Trigger comprehensive discovery
        result = self.client.discover_all_services(address)
        
        if "error" in result:
            return f"**Discovery Status:** ❌ Discovery failed: {result['error']}", {}, gr.Dropdown(choices=[]), "{}", "**Discovery Statistics**\n\nNo data available"
        
        # Store the service data
        self.service_data[address] = result
        
        # Create service tree view
        service_tree = self._create_service_tree(result)
        
        # Create service dropdown choices
        service_choices = [(f"{service['uuid']} ({self._get_service_name(service['uuid'])})", service['uuid']) 
                          for service in result.get('services', [])]
        service_dropdown = gr.Dropdown(choices=service_choices)
        
        # Create raw data view
        raw_data = json.dumps(result, indent=2)
        
        # Create statistics
        stats = self._create_statistics(result)
        
        status = f"**Discovery Status:** ✅ Discovered {result.get('services_count', 0)} services, {result.get('total_characteristics', 0)} characteristics, {result.get('total_descriptors', 0)} descriptors"
        
        return status, service_tree, service_dropdown, raw_data, stats
    
    def on_service_selected_unified(self, selected_device: str, manual_address: str, service_uuid: str) -> Tuple[Dict, gr.Dropdown]:
        """Handle service selection with unified address"""
        address = selected_device if selected_device else manual_address
        return self.on_service_selected(address, service_uuid)
    
    def on_characteristic_selected_unified(self, selected_device: str, manual_address: str, char_uuid: str) -> Tuple[Dict, gr.Dropdown]:
        """Handle characteristic selection with unified address"""
        address = selected_device if selected_device else manual_address
        return self.on_characteristic_selected(address, char_uuid)
    
    def on_descriptor_selected_unified(self, selected_device: str, manual_address: str, desc_uuid: str) -> Dict:
        """Handle descriptor selection with unified address"""
        address = selected_device if selected_device else manual_address
        return self.on_descriptor_selected(address, desc_uuid)
    
    def on_service_selected(self, address: str, service_uuid: str) -> Tuple[Dict, gr.Dropdown]:
        """Handle service selection"""
        if not address or not service_uuid or address not in self.service_data:
            return {}, gr.Dropdown(choices=[])
        
        # Find the selected service
        services = self.service_data[address].get('services', [])
        selected_service = next((s for s in services if s['uuid'] == service_uuid), None)
        
        if not selected_service:
            return {}, gr.Dropdown(choices=[])
        
        # Create service info
        service_info = {
            "uuid": selected_service['uuid'],
            "name": self._get_service_name(selected_service['uuid']),
            "handle": selected_service.get('handle'),
            "primary": selected_service.get('primary', True),
            "characteristics_count": len(selected_service.get('characteristics', []))
        }
        
        # Create characteristic dropdown
        char_choices = [(f"{char['uuid']} ({self._get_characteristic_name(char['uuid'])})", char['uuid']) 
                       for char in selected_service.get('characteristics', [])]
        char_dropdown = gr.Dropdown(choices=char_choices)
        
        return service_info, char_dropdown
    
    def on_characteristic_selected(self, address: str, char_uuid: str) -> Tuple[Dict, gr.Dropdown]:
        """Handle characteristic selection"""
        if not address or not char_uuid or address not in self.service_data:
            return {}, gr.Dropdown(choices=[])
        
        # Find the selected characteristic
        selected_char = None
        for service in self.service_data[address].get('services', []):
            for char in service.get('characteristics', []):
                if char['uuid'] == char_uuid:
                    selected_char = char
                    break
            if selected_char:
                break
        
        if not selected_char:
            return {}, gr.Dropdown(choices=[])
        
        # Create characteristic info
        char_info = {
            "uuid": selected_char['uuid'],
            "name": self._get_characteristic_name(selected_char['uuid']),
            "handle": selected_char.get('handle'),
            "properties": selected_char.get('properties', []),
            "descriptors_count": len(selected_char.get('descriptors', []))
        }
        
        # Create descriptor dropdown
        desc_choices = [(f"{desc['uuid']} ({self._get_descriptor_name(desc['uuid'])})", desc['uuid']) 
                       for desc in selected_char.get('descriptors', [])]
        desc_dropdown = gr.Dropdown(choices=desc_choices)
        
        return char_info, desc_dropdown
    
    def on_descriptor_selected(self, address: str, desc_uuid: str) -> Dict:
        """Handle descriptor selection"""
        if not address or not desc_uuid or address not in self.service_data:
            return {}
        
        # Find the selected descriptor
        selected_desc = None
        for service in self.service_data[address].get('services', []):
            for char in service.get('characteristics', []):
                for desc in char.get('descriptors', []):
                    if desc['uuid'] == desc_uuid:
                        selected_desc = desc
                        break
                if selected_desc:
                    break
            if selected_desc:
                break
        
        if not selected_desc:
            return {}
        
        # Create descriptor info
        desc_info = {
            "uuid": selected_desc['uuid'],
            "name": self._get_descriptor_name(selected_desc['uuid']),
            "handle": selected_desc.get('handle'),
            "type": self._get_descriptor_type(selected_desc['uuid'])
        }
        
        return desc_info
    
    def _create_service_tree(self, data: Dict) -> Dict:
        """Create a hierarchical tree view of services"""
        if not data.get('services'):
            return {"message": "No services discovered"}
        
        tree = {
            "device_address": data['address'],
            "services": []
        }
        
        for service in data['services']:
            service_node = {
                "uuid": service['uuid'],
                "name": self._get_service_name(service['uuid']),
                "handle": service.get('handle'),
                "primary": service.get('primary', True),
                "characteristics": []
            }
            
            for char in service.get('characteristics', []):
                char_node = {
                    "uuid": char['uuid'],
                    "name": self._get_characteristic_name(char['uuid']),
                    "handle": char.get('handle'),
                    "properties": char.get('properties', []),
                    "descriptors": []
                }
                
                for desc in char.get('descriptors', []):
                    desc_node = {
                        "uuid": desc['uuid'],
                        "name": self._get_descriptor_name(desc['uuid']),
                        "handle": desc.get('handle')
                    }
                    char_node["descriptors"].append(desc_node)
                
                service_node["characteristics"].append(char_node)
            
            tree["services"].append(service_node)
        
        return tree
    
    def _create_statistics(self, data: Dict) -> str:
        """Create statistics summary"""
        if not data.get('services'):
            return "**Discovery Statistics**\n\nNo data available"
        
        services_count = data.get('services_count', 0)
        total_chars = data.get('total_characteristics', 0)
        total_descs = data.get('total_descriptors', 0)
        
        # Count properties
        property_counts = {}
        for service in data.get('services', []):
            for char in service.get('characteristics', []):
                for prop in char.get('properties', []):
                    property_counts[prop] = property_counts.get(prop, 0) + 1
        
        stats = f"""**Discovery Statistics**

📊 **Summary**
- **Services:** {services_count}
- **Characteristics:** {total_chars}
- **Descriptors:** {total_descs}

🔧 **Characteristic Properties**
"""
        
        for prop, count in sorted(property_counts.items()):
            stats += f"- **{prop.capitalize()}:** {count}\n"
        
        return stats
    
    def _get_service_name(self, uuid: str) -> str:
        """Get human-readable service name"""
        service_names = {
            "00001800-0000-1000-8000-00805f9b34fb": "Generic Access",
            "00001801-0000-1000-8000-00805f9b34fb": "Generic Attribute",
            "0000180a-0000-1000-8000-00805f9b34fb": "Device Information",
            "0000180f-0000-1000-8000-00805f9b34fb": "Battery Service",
            "00001812-0000-1000-8000-00805f9b34fb": "Human Interface Device",
            "0000181a-0000-1000-8000-00805f9b34fb": "Environmental Sensing",
            "0000fe59-0000-1000-8000-00805f9b34fb": "Nordic UART Service"
        }
        return service_names.get(uuid, "Unknown Service")
    
    def _get_characteristic_name(self, uuid: str) -> str:
        """Get human-readable characteristic name"""
        char_names = {
            "00002a00-0000-1000-8000-00805f9b34fb": "Device Name",
            "00002a01-0000-1000-8000-00805f9b34fb": "Appearance",
            "00002a04-0000-1000-8000-00805f9b34fb": "Peripheral Preferred Connection Parameters",
            "00002a05-0000-1000-8000-00805f9b34fb": "Service Changed",
            "00002a19-0000-1000-8000-00805f9b34fb": "Battery Level",
            "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name String",
            "00002a24-0000-1000-8000-00805f9b34fb": "Model Number String",
            "00002a25-0000-1000-8000-00805f9b34fb": "Serial Number String",
            "00002a27-0000-1000-8000-00805f9b34fb": "Hardware Revision String",
            "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Revision String",
            "00002a28-0000-1000-8000-00805f9b34fb": "Software Revision String",
            "6e400002-b5a3-f393-e0a9-e50e24dcca9e": "Nordic UART TX",
            "6e400003-b5a3-f393-e0a9-e50e24dcca9e": "Nordic UART RX"
        }
        return char_names.get(uuid, "Unknown Characteristic")
    
    def _get_descriptor_name(self, uuid: str) -> str:
        """Get human-readable descriptor name"""
        desc_names = {
            "00002900-0000-1000-8000-00805f9b34fb": "Characteristic Extended Properties",
            "00002901-0000-1000-8000-00805f9b34fb": "Characteristic User Description",
            "00002902-0000-1000-8000-00805f9b34fb": "Client Characteristic Configuration",
            "00002903-0000-1000-8000-00805f9b34fb": "Server Characteristic Configuration",
            "00002904-0000-1000-8000-00805f9b34fb": "Characteristic Presentation Format",
            "00002905-0000-1000-8000-00805f9b34fb": "Characteristic Aggregate Format"
        }
        return desc_names.get(uuid, "Unknown Descriptor")
    
    def _get_descriptor_type(self, uuid: str) -> str:
        """Get descriptor type information"""
        desc_types = {
            "00002900-0000-1000-8000-00805f9b34fb": "Extended Properties",
            "00002901-0000-1000-8000-00805f9b34fb": "User Description",
            "00002902-0000-1000-8000-00805f9b34fb": "Client Configuration",
            "00002903-0000-1000-8000-00805f9b34fb": "Server Configuration",
            "00002904-0000-1000-8000-00805f9b34fb": "Presentation Format",
            "00002905-0000-1000-8000-00805f9b34fb": "Aggregate Format"
        }
        return desc_types.get(uuid, "Unknown Type")