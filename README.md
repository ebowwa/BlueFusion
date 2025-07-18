# BlueFusion 🔵

AI-powered dual BLE interface controller combining MacBook's native BLE with USB sniffer dongles.

## Project Structure

```
BlueFusion/
├── bluefusion.py          # Main CLI entry point
├── src/
│   ├── api/
│   │   └── fastapi_server.py    # REST API server
│   ├── ui/
│   │   └── gradio_interface.py  # Web UI
│   ├── interfaces/
│   │   ├── base.py              # Base interface classes
│   │   ├── macbook_ble.py       # MacBook BLE implementation
│   │   └── sniffer_dongle.py    # USB sniffer implementation
│   └── models/                   # Data models
├── tests/                        # Test suite
├── examples/                     # Example scripts
└── docs/                         # Documentation
```

## Quick Start

### Installation

```bash
# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev,ai]"
```

### Usage

#### Start Everything
```bash
# Start both API and UI
python bluefusion.py start

# API only (no UI)
python bluefusion.py start --no-ui

# Custom ports
python bluefusion.py start --api-port 8080 --ui-port 7000
```

#### Individual Components
```bash
# Start API server only
python bluefusion.py api

# Start UI only
python bluefusion.py ui

# Quick BLE scan
python bluefusion.py scan

# Run tests
python bluefusion.py test
```

#### Using the CLI
```bash
# After installation
bluefusion start
bluefusion scan
bluefusion --help
```

## Features

- **Dual Interface**: Simultaneous control of MacBook BLE and USB sniffer
- **REST API**: Full-featured API with FastAPI (auto-docs at `/docs`)
- **Web UI**: Interactive Gradio interface for monitoring and control
- **Real-time Streaming**: WebSocket support for live packet streaming
- **CLI Tools**: Command-line utilities for quick operations

## API Endpoints

- `GET /` - Status and interface information
- `POST /scan/start` - Start BLE scanning
- `POST /scan/stop` - Stop scanning
- `GET /devices` - List discovered devices
- `POST /connect/{address}` - Connect to device
- `WebSocket /stream` - Real-time packet stream

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src

# Format code
black src/ tests/

# Lint
ruff check src/
```

## Requirements

- Python 3.9+
- macOS (for MacBook BLE interface)
- BLE sniffer dongle (optional, for enhanced monitoring)

## License

MIT