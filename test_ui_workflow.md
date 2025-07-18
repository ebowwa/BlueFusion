# BlueFusion UI Testing Workflow

## To See Devices in the UI:

1. **Open BlueFusion UI**
   - Navigate to http://localhost:7860

2. **Start Scanning (Control Tab)**
   - Go to the "Control" tab
   - Select Interface: "Both" (or MacBook/Sniffer)
   - Select Scan Mode: "Active"
   - Click "Start Scan" button
   - You should see "Scan Status: Scanning started successfully"

3. **View Devices (Devices Tab)**
   - Go to the "Devices" tab
   - Click "Refresh Devices" button
   - You should now see a table of discovered devices

4. **Use Service Explorer**
   - Go to the "Service Explorer" tab
   - Click "🔄 Refresh Device List"
   - Select a device from the dropdown
   - Click "📋 Copy Address" to copy the address
   - Click "Connect" to connect to the device
   - Click "Discover All Services" to explore GATT services

## Troubleshooting:

- If no devices appear:
  1. Make sure you started scanning in the Control tab first
  2. Wait a few seconds for devices to be discovered
  3. Click "Refresh Devices" again

- The API is working correctly (verified via curl commands)
- The issue is likely just the workflow - you need to start scanning before devices will appear

## Quick Test via API:
```bash
# Start scanning
curl -X POST http://localhost:8000/scan/start -H "Content-Type: application/json" -d '{"interface": "both", "mode": "active"}'

# Check devices (after a few seconds)
curl http://localhost:8000/devices | jq '.macbook | length'
```