# BlueFusion Tests

## Running the Tests

### Install test dependencies
```bash
pip install -e ".[dev]"
```

### Run FastAPI tests
```bash
pytest tests/test_fastapi.py -v
```

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Structure

- `test_fastapi.py` - Tests for the FastAPI endpoints
- `test_dual_interface.py` - Integration tests for both BLE interfaces
- `test_macbook_ble.py` - Tests for MacBook BLE functionality
- `test_sniffer.py` - Tests for sniffer dongle functionality

## Running the Application

1. Start the FastAPI server:
   ```bash
   python main.py
   ```

2. In another terminal, start the Gradio interface:
   ```bash
   python gradio_app.py
   ```

Or use the combined launcher:
```bash
python start_bluefusion.py
```

Then access:
- FastAPI docs: http://localhost:8000/docs
- Gradio UI: http://localhost:7860