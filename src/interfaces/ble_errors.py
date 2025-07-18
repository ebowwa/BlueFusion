"""
BLE Security Error Codes and Exceptions
Centralized error handling for BLE security operations
"""
from enum import Enum
from typing import Optional


class BLESecurityError(Enum):
    """Standard BLE security error codes"""
    AUTHENTICATION_FAILURE = (0x05, "Authentication failure")
    PIN_OR_KEY_MISSING = (0x06, "PIN or key missing")
    MEMORY_CAPACITY_EXCEEDED = (0x07, "Memory capacity exceeded")
    CONNECTION_TIMEOUT = (0x08, "Connection timeout")
    PAIRING_NOT_SUPPORTED = (0x09, "Pairing not supported")
    PEER_TERMINATED = (0x0C, "Peer user terminated connection")
    INSUFFICIENT_AUTHENTICATION = (0x0F, "Insufficient authentication")
    INSUFFICIENT_ENCRYPTION = (0x10, "Insufficient encryption")
    INSUFFICIENT_AUTHORIZATION = (0x11, "Insufficient authorization")
    
    def __init__(self, code: int, description: str):
        self.code = code
        self.description = description


class BLESecurityException(Exception):
    """Base exception for BLE security errors"""
    def __init__(self, error: BLESecurityError, device_address: Optional[str] = None):
        self.error = error
        self.device_address = device_address
        super().__init__(f"BLE Security Error {error.code:#04x}: {error.description}"
                         f"{f' (Device: {device_address})' if device_address else ''}")


class BLEPairingRequired(BLESecurityException):
    """Raised when pairing is required for operation"""
    pass


class BLEEncryptionRequired(BLESecurityException):
    """Raised when encryption is required for operation"""
    pass


class BLEAuthenticationRequired(BLESecurityException):
    """Raised when authentication is required for operation"""
    pass


def get_security_error(code: int) -> Optional[BLESecurityError]:
    """Get BLE security error by code"""
    for error in BLESecurityError:
        if error.code == code:
            return error
    return None