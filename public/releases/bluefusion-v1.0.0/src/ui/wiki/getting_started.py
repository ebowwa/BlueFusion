#!/usr/bin/env python3
"""
Getting Started wiki content
"""

CONTENT = """# Getting Started with BlueFusion

## Overview
BlueFusion is a dual-interface BLE monitoring system that combines MacBook native BLE capabilities with USB sniffer dongles for comprehensive Bluetooth Low Energy analysis.

## Quick Start
1. **Start the API Server**: Run the FastAPI server on port 8000
2. **Launch the UI**: Access the Gradio interface on port 7860
3. **Configure Interfaces**: Choose between MacBook, Sniffer, or Both interfaces
4. **Select Scan Mode**: Choose Active or Passive scanning
5. **Start Monitoring**: Click "Start Scan" to begin BLE monitoring

## Interface Selection
- **MacBook**: Uses native macOS BLE capabilities
- **Sniffer**: Uses USB BLE sniffer dongle (requires hardware)
- **Both**: Combines both interfaces for comprehensive coverage
"""