# Hex Pattern Matcher

The Hex Pattern Matcher is a powerful feature in BlueFusion that analyzes BLE characteristic data to find repeating patterns, sequences, and encodings.

## Features

### 1. Pattern Detection
- **Repeating Patterns**: Finds hex sequences that appear multiple times in the data
- **Variable Length**: Supports patterns from 2 to 32 bytes (configurable)
- **Overlapping Detection**: Handles patterns that may overlap in the data
- **Coverage Analysis**: Calculates what percentage of data is covered by patterns

### 2. Sequence Detection
- **Arithmetic Sequences**: Detects incrementing/decrementing byte values
- **Multi-byte Sequences**: Finds patterns in uint16, uint32 values
- **Endianness Support**: Handles both little and big endian data

### 3. Encoding Detection
- **ASCII**: Detects printable ASCII text
- **UTF-8**: Identifies UTF-8 encoded strings
- **BCD**: Recognizes Binary Coded Decimal values
- **Confidence Scoring**: Provides confidence levels for each encoding

### 4. Bit-Level Analysis
- **Bit Patterns**: Finds patterns at the bit level
- **Bit Masks**: Useful for detecting flags and masks in data

### 5. Data Analysis
- **Entropy Calculation**: Measures randomness in the data (0=uniform, 1=random)
- **Frequency Analysis**: Counts pattern occurrences
- **Position Tracking**: Records where each pattern appears

## Usage

### UI Integration

1. **Service Explorer**: Connect to a BLE device and discover services
2. **Characteristic Monitor**: Select a characteristic to monitor
3. **Pattern Analysis**: View real-time pattern detection as data changes

### Pattern Matcher Settings

- **Minimum Pattern Length**: Smallest pattern size to detect (default: 2 bytes)
- **Maximum Pattern Length**: Largest pattern size to detect (default: 32 bytes)
- **Monitor Interval**: How often to read characteristic values (0.1-10 seconds)

### Display Modes

1. **Current Value**: Shows hex dump with ASCII representation
2. **Pattern Analysis**: Lists detected patterns with counts and coverage
3. **Value History**: Tracks changes over time
4. **Advanced Analysis**: Shows sequences, encodings, and bit patterns

## Examples

### Example 1: Heart Rate Sensor
```
Data: 00 48 02 D0 02 E0
Patterns: None (data too short/unique)
Encoding: Binary data
```

### Example 2: Device Name
```
Data: 42 6C 75 65 46 75 73 69 6F 6E 2D 30 30 31
ASCII: BlueFusion-001
Patterns: None (text data)
Encoding: ASCII/UTF-8 (100% confidence)
```

### Example 3: Counter Data
```
Data: 01 02 03 04 05 06 07 08
Sequence: Arithmetic, start=1, increment=1, length=8
Patterns: Sequential pattern detected
```

### Example 4: Repeating Command
```
Data: CA FE CA FE CA FE 00 FF CA FE
Pattern: CAFE (4 times)
Coverage: 80%
Entropy: 0.22 (low randomness)
```

## API Integration

### Read Characteristic
```python
# Read a characteristic value
result = client.read_characteristic(address, char_uuid)
value = bytes.fromhex(result["value"])
```

### Analyze Patterns
```python
from src.analyzers.hex_pattern_matcher import HexPatternMatcher

matcher = HexPatternMatcher()
analysis = matcher.analyze(value)

print(f"Patterns found: {len(analysis.patterns)}")
print(f"Most frequent: {analysis.most_frequent}")
print(f"Coverage: {analysis.coverage:.1%}")
```

## Use Cases

1. **Protocol Reverse Engineering**: Identify command patterns in proprietary protocols
2. **Data Validation**: Detect expected patterns in sensor data
3. **Security Analysis**: Find encryption patterns or keys in data
4. **Debugging**: Visualize data structure and format
5. **Performance Monitoring**: Track changes in characteristic values over time

## Technical Details

### Pattern Matching Algorithm
- Sliding window approach for efficiency
- Hash-based pattern storage for fast lookup
- Filtering to remove redundant sub-patterns

### Performance
- Real-time analysis for data up to 1KB
- Efficient memory usage with pattern deduplication
- Configurable pattern length limits

### Limitations
- Maximum data size: 4KB per analysis
- Pattern length: 2-64 bytes
- History retention: 100-1000 entries (configurable)