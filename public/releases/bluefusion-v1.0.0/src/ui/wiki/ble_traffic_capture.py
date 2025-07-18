#!/usr/bin/env python3
"""
BLE Traffic Capture Techniques wiki content
"""

CONTENT = """# BLE Traffic Capture and Analysis

## Overview

BlueFusion provides a modern, intelligent alternative to Wireshark for BLE traffic analysis, offering reduced friction and enhanced capabilities. This guide covers essential techniques for capturing and analyzing Bluetooth Low Energy traffic, building on methodologies developed by security researchers.

## Essential Hardware for BLE Traffic Capture

### Required Equipment

To effectively capture BLE traffic, you'll need the following hardware components:

1. **Central Device Options**
   - **Android Device**: Preferred for HCI snoop logging capabilities
   - **iOS Device**: Limited capture options but useful for testing
   - **Linux Computer**: Most flexible for advanced capture scenarios

2. **Bluetooth Dongles**
   - **Standard Bluetooth Adapter**: Basic connectivity and HCI access
   - **CSR-based Dongles**: Support for monitor mode
   - **Broadcom-based Adapters**: Good Linux driver support

3. **Specialized BLE Sniffers**
   - **Ubertooth One**
     - Open-source wireless development platform
     - Designed specifically for Bluetooth experimentation
     - Capable of following frequency hopping
     - Price: ~$125
   
   - **Nordic nRF52840 Dongle**
     - Professional-grade BLE development tool
     - Excellent packet capture capabilities
     - Native support for all BLE PHYs
     - Price: ~$10-20

   - **TI CC2540 USB Dongle**
     - Budget-friendly option
     - Good for basic packet sniffing
     - Requires specific firmware
     - Price: ~$50

## BLE Traffic Capture Methods

### Method 1: Host Controller Interface (HCI) Capture

**Advantages:**
- Captures clean, unencrypted data
- No packet loss
- Complete bidirectional traffic
- Works with encrypted connections

**Disadvantages:**
- Requires control over the device
- Limited to one side of the communication

#### Android HCI Snoop Log

1. **Enable Developer Options**
   ```
   Settings → About Phone → Tap "Build Number" 7 times
   ```

2. **Enable Bluetooth HCI Snoop Log**
   ```
   Settings → Developer Options → Enable "Bluetooth HCI snoop log"
   ```

3. **Capture Traffic**
   - Perform the BLE operations you want to analyze
   - All Bluetooth traffic is logged automatically

4. **Retrieve Log File**
   
   **For Non-Rooted Devices:**
   ```bash
   adb bugreport > bugreport.zip
   # Extract btsnoop_hci.log from the zip file
   ```
   
   **For Rooted Devices:**
   ```bash
   adb pull /sdcard/btsnoop_hci.log
   # Or from /data/misc/bluetooth/logs/
   ```

5. **Analyze with BlueFusion**
   ```python
   # BlueFusion can directly import HCI logs
   bluefusion analyze --hci-log btsnoop_hci.log
   ```

#### Linux HCI Capture with btmon

```bash
# Start HCI monitoring
sudo btmon -w capture.btsnoop

# In another terminal, perform BLE operations
# Press Ctrl+C to stop capture

# Analyze with BlueFusion
bluefusion analyze --btsnoop capture.btsnoop
```

### Method 2: Over-the-Air (OTA) Capture

**Advantages:**
- No device access required
- Can capture from any BLE device
- Observes real-world conditions

**Disadvantages:**
- May miss packets due to interference
- Encrypted data requires additional work
- Channel hopping challenges

#### Ubertooth One Setup

1. **Install Ubertooth Tools**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ubertooth ubertooth-firmware
   
   # macOS
   brew install ubertooth
   ```

2. **Update Firmware**
   ```bash
   ubertooth-dfu -d bluetooth_rxtx.dfu -r
   ```

3. **Basic Capture**
   ```bash
   # Follow all BLE connections
   ubertooth-btle -f
   
   # Target specific device (more reliable)
   ubertooth-btle -t aa:bb:cc:dd:ee:ff
   ```

4. **Pipe to Wireshark or BlueFusion**
   ```bash
   # Real-time analysis with Wireshark
   mkfifo /tmp/pipe
   ubertooth-btle -f -c /tmp/pipe &
   wireshark -k -i /tmp/pipe
   
   # Save for BlueFusion analysis
   ubertooth-btle -t aa:bb:cc:dd:ee:ff -c capture.pcap
   bluefusion analyze --pcap capture.pcap
   ```

#### Nordic nRF Sniffer

1. **Flash Sniffer Firmware**
   ```bash
   # Download sniffer firmware from Nordic
   nrfjprog --program sniffer_nrf52840_x.x.x.hex --chiperase
   ```

2. **Install Python Interface**
   ```bash
   pip install pyserial
   # Extract Nordic sniffer package
   ```

3. **Capture with BlueFusion Integration**
   ```python
   # BlueFusion supports direct nRF sniffer integration
   bluefusion capture --interface nrf52840 --channel 37
   ```

### Method 3: BlueFusion Native Capture

BlueFusion provides integrated capture capabilities that surpass traditional tools:

#### MacBook Native BLE Capture
```bash
# Use built-in Bluetooth hardware
bluefusion capture --interface native --mode promiscuous

# Target specific device
bluefusion capture --interface native --target aa:bb:cc:dd:ee:ff
```

#### USB Sniffer Integration
```bash
# Auto-detect and use connected sniffers
bluefusion capture --auto-detect

# Specify sniffer type
bluefusion capture --interface ubertooth --follow-device aa:bb:cc:dd:ee:ff
```

## Analyzing Captured Traffic

### BlueFusion Analysis Features

#### Intelligent Protocol Parsing
```bash
# Automatic protocol detection and parsing
bluefusion analyze capture.pcap --deep-inspection

# Export analysis results
bluefusion analyze capture.pcap --export-format json > analysis.json
```

#### Advanced Filtering
```python
# Filter by service UUID
bluefusion filter --service-uuid 0x180D  # Heart Rate Service

# Filter by characteristic
bluefusion filter --characteristic-uuid 0x2A37  # Heart Rate Measurement

# Complex queries
bluefusion query "packets where att.opcode == 'Write' and data contains 'password'"
```

### Wireshark Integration

While BlueFusion offers superior BLE analysis, it maintains Wireshark compatibility:

#### Essential Wireshark Filters
```
# BLE ATT protocol filter
btatt

# Specific opcodes
btatt.opcode == 0x12  # Write Request

# Service/Characteristic filtering
btatt.uuid16 == 0x180f  # Battery Service

# Advertisement packets
btle.advertising_header.pdu_type == 0x00
```

#### Wireshark BLE Menu Navigation
- **Wireless → Bluetooth ATT Server Attributes**
  - View complete GATT database
  - See all UUIDs and handles
  - Understand device structure

### Traffic Analysis Best Practices

#### 1. Capture Strategy
- **Lock to Target Device**: Reduces packet loss
- **Use Multiple Channels**: Some sniffers support parallel capture
- **Minimize Interference**: Disable WiFi if possible
- **Capture During Pairing**: Critical for security analysis

#### 2. Analysis Workflow
1. **Initial Overview**: Identify devices and connection events
2. **Service Discovery**: Map out GATT structure
3. **Data Flow Analysis**: Track read/write/notify patterns
4. **Security Assessment**: Check encryption and authentication
5. **Anomaly Detection**: Identify unusual patterns

#### 3. Common Analysis Targets

**Authentication Flows**
```python
# BlueFusion authentication analysis
bluefusion analyze --focus authentication capture.pcap
```

**Data Leakage**
```python
# Search for sensitive data patterns
bluefusion search --patterns "password|token|key|secret" capture.pcap
```

**Replay Attack Vectors**
```python
# Identify replayable commands
bluefusion analyze --replay-detection capture.pcap
```

## BlueFusion Advantages Over Wireshark

### 1. BLE-Specific Intelligence
- Automatic GATT database reconstruction
- Smart characteristic value interpretation
- Protocol-aware anomaly detection

### 2. Integrated Capture and Analysis
- No need for separate capture tools
- Unified workflow from capture to report
- Real-time analysis during capture

### 3. Security-Focused Features
- Automatic vulnerability detection
- Pairing security analysis
- Cryptographic weakness identification

### 4. Modern User Experience
- Web-based UI with real-time updates
- REST API for automation
- Export to multiple formats

### 5. Advanced Capabilities
- Machine learning-based pattern recognition
- Automated device fingerprinting
- Cross-capture correlation

## Practical Examples

### Example 1: Capturing Fitness Tracker Data

```bash
# Start BlueFusion in auto-discovery mode
bluefusion discover --duration 30

# Target the fitness tracker
bluefusion capture --target "FitBand-1234" --duration 300

# Analyze heart rate data
bluefusion analyze --service "Heart Rate" last-capture.bf

# Export readable report
bluefusion report --format html > fitness-tracker-analysis.html
```

### Example 2: Smart Lock Security Audit

```bash
# Comprehensive security capture
bluefusion security-audit --device "SmartLock-ABCD" \
  --tests "pairing,replay,fuzzing" \
  --duration 600

# Generate security report
bluefusion security-report --severity high last-audit.bf
```

### Example 3: IoT Device Reverse Engineering

```python
# Python script using BlueFusion library
import bluefusion

# Initialize capture
bf = bluefusion.Capture(interface='ubertooth')
bf.set_target('aa:bb:cc:dd:ee:ff')

# Capture with callbacks
def on_write(packet):
    if packet.is_write_request():
        print(f"Write to {packet.handle}: {packet.value.hex()}")

bf.on_packet(on_write)
bf.start(duration=300)

# Analyze results
analysis = bf.analyze()
print(analysis.get_command_summary())
```

## Troubleshooting Common Issues

### Channel Hopping Synchronization
- Use device MAC address locking
- Increase Ubertooth frequency tolerance
- Consider using multiple sniffers

### Encrypted Traffic
- Capture during pairing process
- Use HCI logs when possible
- Apply known keys if available

### Packet Loss
- Reduce interference sources
- Use higher-quality antennas
- Position sniffer optimally
- Consider using multiple capture points

## Security Considerations

### Legal and Ethical Guidelines
- Only analyze devices you own or have permission to test
- Respect privacy laws in your jurisdiction
- Do not interfere with medical devices
- Document your testing authorization

### Responsible Disclosure
- Report vulnerabilities to manufacturers
- Allow reasonable time for fixes
- Consider coordinated disclosure
- Document findings professionally

## Next Steps

1. **Practice with Test Devices**: Start with your own BLE peripherals
2. **Build a Capture Lab**: Invest in quality sniffing hardware
3. **Develop Analysis Skills**: Learn GATT protocol internals
4. **Contribute to BlueFusion**: Share captures and analysis scripts
5. **Join the Community**: Participate in BLE security research

BlueFusion transforms BLE traffic analysis from a complex, tool-heavy process into an streamlined, intelligent workflow. By combining capture, analysis, and reporting in a single platform, it enables security researchers and developers to focus on understanding BLE communications rather than wrestling with tools."""