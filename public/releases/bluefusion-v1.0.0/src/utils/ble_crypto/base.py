"""
Base classes for BLE cryptography utilities
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BLEDecryptionError(Exception):
    """Base exception for BLE decryption errors"""
    pass


class BLEDecryptorBase(ABC):
    """Base class for BLE decryption algorithms"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
        **kwargs
    ) -> Optional[bytes]:
        """
        Decrypt BLE data using the specific algorithm.
        
        Args:
            key: Encryption key
            nonce: Nonce/IV for decryption
            ciphertext: Encrypted data
            associated_data: Additional authenticated data
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Return the name of the decryption algorithm"""
        pass
    
    def parse_encrypted_pdu(
        self,
        pdu: bytes,
        tag_length: int = 4
    ) -> Tuple[Optional[bytes], Optional[bytes], Optional[bytes]]:
        """
        Parse an encrypted BLE PDU into components.
        
        Args:
            pdu: Complete encrypted PDU
            tag_length: Expected authentication tag length
            
        Returns:
            Tuple of (header, payload, mic) or (None, None, None) if invalid
        """
        if len(pdu) < 3 + tag_length:
            self.logger.error(f"PDU too short: {len(pdu)} bytes")
            return None, None, None
        
        try:
            import struct
            
            # BLE PDU structure: Header (1) + Length (2) + Payload + MIC
            header = pdu[0:1]
            length = struct.unpack("<H", pdu[1:3])[0]
            
            if len(pdu) < 3 + length + tag_length:
                self.logger.error(f"PDU length mismatch: expected {3 + length + tag_length}, got {len(pdu)}")
                return None, None, None
            
            payload = pdu[3:3+length]
            mic = pdu[3+length:3+length+tag_length]
            
            return header, payload, mic
            
        except Exception as e:
            self.logger.error(f"Failed to parse PDU: {e}")
            return None, None, None