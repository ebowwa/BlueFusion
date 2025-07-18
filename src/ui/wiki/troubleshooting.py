#!/usr/bin/env python3
"""
Troubleshooting wiki content
"""

CONTENT = """# Troubleshooting

## Common Issues

### API Server Not Running
- **Symptoms**: Connection errors, empty data
- **Solution**: Ensure FastAPI server is running on port 8000
- **Check**: Visit http://localhost:8000/docs for API documentation

### No Devices Found
- **Symptoms**: Empty device list despite scanning
- **Solutions**:
  - Check interface selection (MacBook vs Sniffer)
  - Verify BLE devices are advertising nearby
  - Try different scan modes (Active/Passive)
  - Check channel settings for sniffer interface

### Sniffer Not Working
- **Symptoms**: Sniffer interface shows no data
- **Solutions**:
  - Verify USB sniffer hardware is connected
  - Check device drivers and permissions
  - Try different USB ports
  - Restart the API server

### Performance Issues
- **Symptoms**: Slow UI updates, high CPU usage
- **Solutions**:
  - Reduce refresh interval
  - Limit number of displayed packets
  - Close unnecessary browser tabs
  - Restart the application

## Getting Help
- Check the API documentation at http://localhost:8000/docs
- Review log files for error messages
- Verify hardware connections and permissions
"""