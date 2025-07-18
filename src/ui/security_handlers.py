#!/usr/bin/env python3
"""
Security Handlers for BlueFusion UI
Manages BLE security interactions in the Gradio interface
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Tuple
import gradio as gr
from datetime import datetime


class SecurityHandlers:
    """Handles security operations in the UI"""
    
    def __init__(self):
        self.pending_pairing: Dict[str, Dict[str, Any]] = {}
        self.pairing_callbacks: Dict[str, Callable] = {}
    
    def format_security_status(self, device_info: Dict[str, Any]) -> str:
        """Format device security status for display"""
        address = device_info.get("address", "Unknown")
        bonded = device_info.get("bonded", False)
        security_level = device_info.get("security_level", "None")
        
        status = f"**Device: {address}**\n"
        status += f"- Bonded: {'Yes' if bonded else 'No'}\n"
        status += f"- Security Level: {security_level}\n"
        
        if device_info.get("requires_pairing"):
            status += f"- **Pairing Required**\n"
        
        return status
    
    def handle_pairing_request(self, device_address: str, pairing_type: str) -> Tuple[str, bool, str]:
        """Handle incoming pairing request"""
        self.pending_pairing[device_address] = {
            "type": pairing_type,
            "timestamp": datetime.now(),
            "status": "pending"
        }
        
        if pairing_type == "passkey_entry":
            message = f"Device {device_address} requires a 6-digit passkey"
            show_input = True
            input_label = "Enter 6-digit passkey"
        elif pairing_type == "numeric_comparison":
            message = f"Device {device_address} shows code: 123456\nDo you confirm this matches?"
            show_input = False
            input_label = ""
        else:  # just_works
            message = f"Device {device_address} requests pairing"
            show_input = False
            input_label = ""
        
        return message, show_input, input_label
    
    def submit_pairing_response(self, device_address: str, response: str, pairing_type: str) -> str:
        """Submit pairing response"""
        if device_address not in self.pending_pairing:
            return "No pending pairing for this device"
        
        pairing_info = self.pending_pairing[device_address]
        
        if pairing_type == "passkey_entry":
            # Validate passkey
            if not response or not response.isdigit() or len(response) != 6:
                return "Invalid passkey. Please enter a 6-digit number"
            
            pairing_info["response"] = response
            pairing_info["status"] = "completed"
            
            # Trigger callback if registered
            if device_address in self.pairing_callbacks:
                self.pairing_callbacks[device_address](response)
            
            del self.pending_pairing[device_address]
            return f"Passkey sent for {device_address}"
        
        elif pairing_type == "numeric_comparison":
            pairing_info["response"] = response.lower() == "yes"
            pairing_info["status"] = "completed"
            
            if device_address in self.pairing_callbacks:
                self.pairing_callbacks[device_address](pairing_info["response"])
            
            del self.pending_pairing[device_address]
            return f"Pairing {'confirmed' if pairing_info['response'] else 'rejected'} for {device_address}"
        
        else:  # just_works
            pairing_info["status"] = "completed"
            
            if device_address in self.pairing_callbacks:
                self.pairing_callbacks[device_address](True)
            
            del self.pending_pairing[device_address]
            return f"Pairing accepted for {device_address}"
    
    def get_bonded_devices(self, bonds: Dict[str, Any]) -> gr.DataFrame:
        """Format bonded devices for display"""
        import pandas as pd
        
        if not bonds:
            return pd.DataFrame({"Info": ["No bonded devices"]})
        
        devices = []
        for address, bond_info in bonds.items():
            devices.append({
                "Address": address,
                "Security Level": bond_info.get("security_level", "Unknown"),
                "Authenticated": "Yes" if bond_info.get("authenticated") else "No",
                "Last Connected": bond_info.get("last_connected", "Never")
            })
        
        return pd.DataFrame(devices)
    
    def remove_bond(self, address: str, security_manager) -> str:
        """Remove bond with a device"""
        if security_manager.remove_bond(address):
            return f"Bond removed for device {address}"
        return f"No bond found for device {address}"


def create_security_ui() -> Dict[str, Any]:
    """Create security UI components for Gradio"""
    components = {}
    
    with gr.Group():
        gr.Markdown("### BLE Security")
        
        with gr.Row():
            components["pairing_status"] = gr.Textbox(
                label="Pairing Status",
                lines=3,
                interactive=False
            )
            
            with gr.Column():
                components["pairing_input"] = gr.Textbox(
                    label="Pairing Input",
                    placeholder="Enter passkey or confirmation",
                    visible=False
                )
                components["pairing_submit"] = gr.Button(
                    "Submit",
                    visible=False
                )
        
        with gr.Row():
            components["bonded_devices"] = gr.DataFrame(
                label="Bonded Devices",
                interactive=False
            )
            
            with gr.Column():
                components["remove_bond_address"] = gr.Textbox(
                    label="Device Address",
                    placeholder="AA:BB:CC:DD:EE:FF"
                )
                components["remove_bond_btn"] = gr.Button("Remove Bond")
        
        components["refresh_bonds_btn"] = gr.Button("Refresh Bonded Devices")
    
    return components