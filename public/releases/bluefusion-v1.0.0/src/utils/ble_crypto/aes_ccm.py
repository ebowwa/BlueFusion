"""
AES-CCM Decryption for BLE

This module provides AES-CCM decryption specifically for Bluetooth Low Energy.
AES-CCM is the standard encryption method used in BLE encrypted connections.
"""

import struct
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.backends import default_backend

from .base import BLEDecryptorBase, BLEDecryptionError


class BLEAESCCMDecryptor(BLEDecryptorBase):
    """AES-CCM decryption for BLE"""
    
    def __init__(self):
        super().__init__()
        self.backend = default_backend()
    
    def get_algorithm_name(self) -> str:
        return "AES-CCM"
    
    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
        tag_length: int = 4
    ) -> Optional[bytes]:
        """
        Decrypt data using AES-CCM (Counter with CBC-MAC).
        
        Args:
            key: 128-bit (16 byte) encryption key
            nonce: 13-byte nonce/IV for BLE
            ciphertext: Encrypted data including the authentication tag
            associated_data: Additional authenticated data (AAD)
            tag_length: Length of authentication tag in bytes (BLE uses 4 bytes)
            
        Returns:
            Decrypted plaintext bytes, or None if decryption fails
        """
        try:
            # Validate inputs
            if len(key) != 16:
                raise BLEDecryptionError(f"Key must be 16 bytes (128 bits), got {len(key)}")
            if len(nonce) != 13:
                raise BLEDecryptionError(f"Nonce must be 13 bytes for BLE, got {len(nonce)}")
            if tag_length not in [4, 6, 8, 10, 12, 14, 16]:
                raise BLEDecryptionError(f"Invalid tag length: {tag_length}")
            
            # Create AES-CCM cipher with specified tag length
            cipher = AESCCM(key, tag_length=tag_length)
            
            # Decrypt and verify
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            
            self.logger.debug(f"Successfully decrypted {len(plaintext)} bytes using AES-CCM")
            return plaintext
            
        except Exception as e:
            self.logger.error(f"AES-CCM decryption failed: {e}")
            return None
    
    def construct_ble_nonce(
        self,
        iv: bytes,
        packet_counter: int,
        is_master_to_slave: bool = True
    ) -> bytes:
        """
        Construct a BLE nonce from IV and packet counter.
        
        Args:
            iv: 8-byte initialization vector from pairing
            packet_counter: 39-bit packet counter value
            is_master_to_slave: Direction bit (True for master->slave)
            
        Returns:
            13-byte nonce for AES-CCM
        """
        if len(iv) != 8:
            raise BLEDecryptionError(f"IV must be 8 bytes, got {len(iv)}")
        if packet_counter >= (1 << 39):
            raise BLEDecryptionError(f"Packet counter too large: {packet_counter}")
        
        # Set direction bit (MSB of the 5-byte counter)
        if is_master_to_slave:
            packet_counter |= (1 << 39)
        
        # Pack as 5 bytes (40 bits total with direction bit)
        counter_bytes = struct.pack("<Q", packet_counter)[:5]
        
        return iv + counter_bytes


# Global instance for convenience functions
_aes_ccm_decryptor = BLEAESCCMDecryptor()


def decrypt_ble_packet_aes_ccm(
    key: bytes,
    iv: bytes,
    packet_counter: int,
    encrypted_pdu: bytes,
    is_master_to_slave: bool = True,
    tag_length: int = 4
) -> Optional[bytes]:
    """
    Decrypt a complete BLE packet using AES-CCM.
    
    Args:
        key: 128-bit encryption key
        iv: 8-byte initialization vector
        packet_counter: Current packet counter
        encrypted_pdu: Complete encrypted PDU
        is_master_to_slave: Direction of communication
        tag_length: Authentication tag length (default 4 for BLE)
        
    Returns:
        Decrypted payload or None if decryption fails
    """
    # Parse PDU
    header, ciphertext_with_tag, _ = _aes_ccm_decryptor.parse_encrypted_pdu(encrypted_pdu, tag_length)
    if header is None:
        return None
    
    # Construct nonce
    nonce = _aes_ccm_decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave)
    
    # Use header as AAD
    aad = header + encrypted_pdu[1:3]  # Header + length field
    
    # Decrypt
    return _aes_ccm_decryptor.decrypt(key, nonce, ciphertext_with_tag, aad, tag_length)


def decrypt_ble_data_channel_aes_ccm(
    ltk: bytes,
    skd_master: bytes,
    skd_slave: bytes,
    encrypted_data: bytes,
    packet_counter: int,
    is_master_to_slave: bool = True
) -> Optional[bytes]:
    """
    Decrypt BLE data channel traffic using AES-CCM and Long Term Key.
    
    Args:
        ltk: Long Term Key from pairing
        skd_master: Session Key Diversifier from master
        skd_slave: Session Key Diversifier from slave
        encrypted_data: Encrypted data payload
        packet_counter: Current packet counter
        is_master_to_slave: Direction of communication
        
    Returns:
        Decrypted data or None if decryption fails
    """
    # Derive session key (SK = LTK for LE Legacy pairing)
    session_key = ltk
    
    # Construct IV from SKD values
    iv = skd_slave + skd_master  # 8 bytes total
    
    # Construct nonce
    nonce = _aes_ccm_decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave)
    
    # Decrypt without AAD for data channel
    return _aes_ccm_decryptor.decrypt(session_key, nonce, encrypted_data, None, 4)