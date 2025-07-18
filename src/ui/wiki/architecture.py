#!/usr/bin/env python3
"""
Technical Architecture wiki content
"""

CONTENT = """# BlueFusion Technical Architecture

## System Overview
BlueFusion is built on a modular architecture that enables simultaneous control of multiple BLE interfaces through a unified API and UI layer.

## Core Components

### 1. Interface Layer (`src/interfaces/`)
- **Base Interface** (`base.py`): Abstract base classes defining the BLE interface contract
- **MacBook BLE** (`macbook_ble.py`): Native macOS CoreBluetooth implementation
- **Sniffer Dongle** (`sniffer_dongle.py`): USB BLE sniffer integration
- **Security Manager** (`security_manager.py`): Handles BLE security protocols
- **Channel Hopper** (`channel_hopper.py`): Manages frequency hopping for sniffers

### 2. Analysis Layer (`src/analyzers/`)
- **Packet Inspector** (`packet_inspector.py`): Real-time packet analysis and filtering
- **Protocol Parsers** (`protocol_parsers/`):
  - `base.py`: Base parser framework
  - `gatt.py`: GATT protocol parsing

### 3. API Layer (`src/api/`)
- **FastAPI Server** (`fastapi_server.py`): RESTful API with WebSocket support
  - Automatic OpenAPI documentation
  - Real-time packet streaming
  - Async request handling

### 4. UI Layer (`src/ui/`)
- **Gradio Interface** (`gradio_interface.py`): Web-based UI
- **WebSocket Handler** (`websocket_handler.py`): Real-time data streaming
- **Data Models** (`data_models.py`): Pydantic models for data validation
- **Visualization** (`visualization.py`): Packet visualization components

### 5. Utilities (`src/utils/`)
- **BLE Crypto** (`ble_crypto/`): Encryption/decryption utilities
  - AES-CCM implementation
  - XOR cipher support
- **Serial Utils** (`serial_utils.py`): Serial port management

## Data Flow Architecture

```
┌─────────────┐     ┌─────────────┐
│ MacBook BLE │     │ USB Sniffer │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
         ┌───────▼────────┐
         │ Interface Base │
         └───────┬────────┘
                 │
         ┌───────▼────────┐
         │ Packet Inspector│
         └───────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐           ┌───────▼────┐
│FastAPI │           │ Gradio UI  │
│  API   │◄─────────►│            │
└────────┘ WebSocket └────────────┘
```

## Key Design Patterns

### 1. Abstract Factory Pattern
- Interface creation through factory methods
- Allows runtime selection of BLE implementation

### 2. Observer Pattern
- Real-time packet notification system
- WebSocket connections for live updates

### 3. Strategy Pattern
- Pluggable protocol parsers
- Extensible analysis framework

### 4. Singleton Pattern
- Single instance of interface managers
- Centralized configuration management

## Thread Safety
- Async/await for non-blocking operations
- Thread-safe queues for packet buffering
- Lock-free data structures where possible

## Security Considerations
- Encrypted packet handling
- Secure WebSocket connections
- Input validation at all layers
- No storage of sensitive data

## Performance Optimizations
- Packet filtering at interface level
- Efficient binary parsing
- Connection pooling for WebSockets
- Lazy loading of UI components
"""