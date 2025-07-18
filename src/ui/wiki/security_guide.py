#!/usr/bin/env python3
"""
Security Guide wiki content
"""

CONTENT = """# BlueFusion Security Guide

## BLE Security Overview

### Security Levels
1. **No Security**: No authentication or encryption
2. **Unauthenticated Pairing**: Encryption without MITM protection
3. **Authenticated Pairing**: Encryption with MITM protection
4. **Authenticated LE Secure Connections**: FIPS-approved algorithms

## Security Manager Features

### Pairing Methods
- **Just Works**: No user interaction required (vulnerable to MITM)
- **Passkey Entry**: 6-digit PIN entry
- **Numeric Comparison**: Verify matching numbers on both devices
- **Out of Band (OOB)**: Exchange keys through alternate channel

### Key Types
- **LTK (Long Term Key)**: Main encryption key
- **IRK (Identity Resolving Key)**: For private address resolution
- **CSRK (Connection Signature Resolving Key)**: For data signing

## Using BlueFusion Security Features

### Monitor Pairing Requests
```python
# Configure security monitoring
security_config = {
    "monitor_pairing": true,
    "log_key_exchange": true,
    "alert_weak_security": true,
    "block_insecure": false
}

# Security event handlers
def on_pairing_request(event):
    print(f"Pairing request from {event['address']}")
    print(f"Method: {event['method']}")
    print(f"IO Capabilities: {event['io_caps']}")
    
def on_encryption_change(event):
    print(f"Encryption changed: {event['enabled']}")
    print(f"Key size: {event['key_size']} bytes")
```

### Analyze Security Vulnerabilities

#### Check for Weak Pairing
```python
def analyze_pairing_security(device):
    vulnerabilities = []
    
    if device['pairing_method'] == 'Just Works':
        vulnerabilities.append({
            'severity': 'HIGH',
            'issue': 'Just Works pairing - No MITM protection',
            'recommendation': 'Use Passkey or Numeric Comparison'
        })
    
    if device['key_size'] < 16:
        vulnerabilities.append({
            'severity': 'MEDIUM',
            'issue': f'Weak key size: {device["key_size"]} bytes',
            'recommendation': 'Use 16-byte keys'
        })
    
    if not device['secure_connections']:
        vulnerabilities.append({
            'severity': 'LOW',
            'issue': 'Legacy pairing used',
            'recommendation': 'Enable LE Secure Connections'
        })
    
    return vulnerabilities
```

#### Detect Privacy Issues
```python
def check_privacy_issues(device):
    issues = []
    
    # Check for static addresses
    if device['address_type'] == 'public' or device['address_type'] == 'static':
        issues.append({
            'issue': 'Device uses trackable address',
            'impact': 'Device can be tracked over time',
            'fix': 'Enable private addressing'
        })
    
    # Check for identifiable data in advertisements
    if 'name' in device['advertisement']:
        if any(pattern in device['advertisement']['name'] 
               for pattern in ['phone', 'user', 'personal']):
            issues.append({
                'issue': 'Potentially sensitive device name',
                'impact': 'May reveal user identity',
                'fix': 'Use generic device names'
            })
    
    return issues
```

## Encryption and Decryption

### Decrypt Captured Packets
```python
# Configure decryption keys
decryption_config = {
    "ltk": "0x1234567890ABCDEF1234567890ABCDEF",
    "ediv": "0x1234",
    "rand": "0x1234567890ABCDEF",
    "irk": "0xFEDCBA0987654321FEDCBA0987654321"
}

# Apply decryption
def decrypt_packet(packet, keys):
    if packet['encrypted']:
        try:
            decrypted = ble_crypto.decrypt_aes_ccm(
                packet['data'],
                keys['ltk'],
                packet['packet_counter'],
                packet['direction']
            )
            return {
                'success': True,
                'data': decrypted,
                'original': packet['data']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original': packet['data']
            }
```

### Key Exchange Analysis
```python
# Monitor key exchange
def analyze_key_exchange(packets):
    key_exchange = {
        'pairing_request': None,
        'pairing_response': None,
        'public_keys': [],
        'dhkey_check': None,
        'key_distribution': []
    }
    
    for packet in packets:
        if packet['type'] == 'SMP_PAIRING_REQUEST':
            key_exchange['pairing_request'] = packet
        elif packet['type'] == 'SMP_PAIRING_RESPONSE':
            key_exchange['pairing_response'] = packet
        elif packet['type'] == 'SMP_PUBLIC_KEY':
            key_exchange['public_keys'].append(packet)
        # ... continue for other SMP packets
    
    return key_exchange
```

## Attack Detection

### Common BLE Attacks

#### 1. MITM Attack Detection
```python
def detect_mitm_indicators(packets):
    indicators = []
    
    # Check for suspicious pairing timing
    pairing_times = extract_pairing_times(packets)
    if any(t < 100 for t in pairing_times):  # Less than 100ms
        indicators.append({
            'type': 'MITM',
            'confidence': 'HIGH',
            'reason': 'Abnormally fast pairing response'
        })
    
    # Check for multiple pairing attempts
    pairing_attempts = count_pairing_attempts(packets)
    if pairing_attempts > 3:
        indicators.append({
            'type': 'MITM',
            'confidence': 'MEDIUM',
            'reason': f'{pairing_attempts} pairing attempts detected'
        })
    
    return indicators
```

#### 2. Replay Attack Detection
```python
def detect_replay_attacks(packets):
    seen_packets = {}
    replay_candidates = []
    
    for packet in packets:
        if packet['encrypted']:
            packet_hash = hash(packet['data'] + packet['counter'])
            
            if packet_hash in seen_packets:
                replay_candidates.append({
                    'original': seen_packets[packet_hash],
                    'replay': packet,
                    'time_delta': packet['timestamp'] - seen_packets[packet_hash]['timestamp']
                })
            else:
                seen_packets[packet_hash] = packet
    
    return replay_candidates
```

#### 3. Jamming Detection
```python
def detect_jamming(channel_stats):
    jamming_indicators = []
    
    for channel, stats in channel_stats.items():
        # High error rate
        if stats['error_rate'] > 0.3:  # 30% errors
            jamming_indicators.append({
                'channel': channel,
                'type': 'high_error_rate',
                'severity': 'HIGH'
            })
        
        # Sudden drop in packets
        if stats['packet_rate_change'] < -0.5:  # 50% drop
            jamming_indicators.append({
                'channel': channel,
                'type': 'packet_rate_drop',
                'severity': 'MEDIUM'
            })
    
    return jamming_indicators
```

## Security Best Practices

### For Device Manufacturers
1. **Always use LE Secure Connections** when possible
2. **Implement proper random number generation**
3. **Use maximum key sizes** (16 bytes)
4. **Enable address privacy** by default
5. **Validate all input data** before processing
6. **Implement rate limiting** for connection attempts

### For Security Auditors
1. **Test all pairing methods** supported by device
2. **Verify encryption is properly implemented**
3. **Check for hardcoded keys** or credentials
4. **Test privacy features** (address randomization)
5. **Analyze update mechanisms** for security
6. **Document all findings** with severity levels

### Security Monitoring Dashboard
```python
# Real-time security monitoring
class SecurityMonitor:
    def __init__(self):
        self.alerts = []
        self.statistics = {
            'total_devices': 0,
            'secure_devices': 0,
            'vulnerable_devices': 0,
            'attacks_detected': 0
        }
    
    def update(self, packet):
        # Check for security events
        if self.is_pairing_packet(packet):
            self.analyze_pairing_security(packet)
        
        if self.is_encrypted(packet):
            self.verify_encryption_strength(packet)
        
        if self.is_suspicious(packet):
            self.create_alert(packet)
    
    def get_security_score(self, device):
        score = 100
        
        # Deduct points for vulnerabilities
        if device['pairing_method'] == 'Just Works':
            score -= 30
        if device['key_size'] < 16:
            score -= 20
        if not device['address_privacy']:
            score -= 15
        if not device['secure_connections']:
            score -= 10
        
        return max(0, score)
```

## Compliance and Standards

### NIST Guidelines
- Use FIPS-approved algorithms
- Minimum 112-bit security strength
- Proper key management practices
- Regular security assessments

### GDPR Considerations
- Monitor for personal data in advertisements
- Ensure proper data anonymization
- Document security measures
- Implement data retention policies

### Industry Standards
- Bluetooth SIG security requirements
- IoT security frameworks
- Medical device regulations (if applicable)
- Financial industry standards (if applicable)
"""