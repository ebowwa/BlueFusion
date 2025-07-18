"""Serial port utility functions."""
import os
import serial
import serial.tools.list_ports
from typing import Optional, List, Dict


def is_port_available(port_path: str) -> bool:
    """
    Check if a serial port is actually available and can be opened.
    
    Args:
        port_path: The path to the serial port (e.g., '/dev/cu.usbmodem101')
        
    Returns:
        bool: True if the port exists and can be opened, False otherwise
    """
    # First check if the device file exists
    if not os.path.exists(port_path):
        return False
    
    # Try to open the port to verify it's actually accessible
    try:
        # Use exclusive=True to prevent opening if already in use (where supported)
        # Note: exclusive parameter may not work on all platforms
        test_conn = serial.Serial()
        test_conn.port = port_path
        test_conn.baudrate = 9600
        test_conn.timeout = 0.1
        
        # Try to set exclusive if supported
        if hasattr(test_conn, 'exclusive'):
            test_conn.exclusive = True
            
        test_conn.open()
        test_conn.close()
        return True
    except (serial.SerialException, OSError, IOError):
        # Port exists but cannot be opened (device disconnected, permission issue, etc.)
        return False


def get_available_serial_ports() -> List[Dict[str, str]]:
    """
    Get a list of all available serial ports with their descriptions.
    
    Returns:
        List of dictionaries containing port information:
        [{'port': '/dev/cu.usbmodem101', 'description': 'USB Modem', 'hwid': '...'}]
    """
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            'port': port.device,
            'description': port.description,
            'hwid': port.hwid
        })
    return ports


def find_ble_sniffer_port() -> Optional[str]:
    """
    Auto-detect BLE sniffer dongles by looking for known keywords and VID/PID combinations.
    
    Returns:
        Optional[str]: The port path if a sniffer is found, None otherwise
    """
    keywords = ['sniffer', 'ble', 'nordic', 'ti', 'bluetooth']
    known_vid_pid = [
        (0x0451, 0x16AA),  # TI CC2540
        (0x1366, 0x0105),  # Nordic nRF51
        (0x1915, 0x520F),  # Nordic nRF52
    ]
    
    for port in serial.tools.list_ports.comports():
        # Check description for keywords
        description_lower = port.description.lower()
        if any(keyword in description_lower for keyword in keywords):
            # Verify the port is actually available
            if is_port_available(port.device):
                return port.device
        
        # Check VID/PID
        if hasattr(port, 'vid') and hasattr(port, 'pid'):
            if (port.vid, port.pid) in known_vid_pid:
                if is_port_available(port.device):
                    return port.device
    
    return None


def verify_serial_connection(serial_conn: Optional[serial.Serial], port_path: Optional[str] = None) -> bool:
    """
    Verify that a serial connection is still valid and the port is available.
    
    Args:
        serial_conn: The serial connection object to verify
        port_path: Optional port path to check (uses serial_conn.port if not provided)
        
    Returns:
        bool: True if connection is valid and port is available, False otherwise
    """
    if serial_conn is None:
        return False
    
    # Get the port from the connection if not provided
    if port_path is None:
        port_path = getattr(serial_conn, 'port', None)
        if port_path is None:
            return False
    
    # Check if the connection object is open and valid
    try:
        # If we have an open connection, we don't need to check port availability
        # as it would try to open the port again which may fail or give false results
        if serial_conn.is_open:
            # Verify the port still exists in the system
            if not os.path.exists(port_path):
                return False
            return True
        else:
            # Connection is closed, check if we can open it
            return is_port_available(port_path)
    except:
        return False