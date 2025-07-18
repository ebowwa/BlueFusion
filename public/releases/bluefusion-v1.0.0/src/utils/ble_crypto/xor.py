"""
XOR Decryption for BLE

This module provides XOR-based decryption commonly used in cheap BLE devices,
particularly from Chinese manufacturers. XOR is a weak obfuscation method
but still widely used due to its simplicity.
"""

from typing import Optional, Union
from .base import BLEDecryptorBase, BLEDecryptionError


class BLEXORDecryptor(BLEDecryptorBase):
    """XOR obfuscation decryption for BLE"""
    
    def get_algorithm_name(self) -> str:
        return "XOR-Obfuscation"
    
    def decrypt(
        self,
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
        **kwargs
    ) -> Optional[bytes]:
        """
        Decrypt data using XOR obfuscation.
        
        Args:
            key: XOR key (variable length)
            nonce: Not used in XOR (placeholder for interface compatibility)
            ciphertext: XOR-encrypted data
            associated_data: Not used in XOR (placeholder)
            **kwargs: Additional parameters (counter_start, use_packet_counter)
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        try:
            if not key:
                raise BLEDecryptionError("XOR key cannot be empty")
            if not ciphertext:
                raise BLEDecryptionError("Ciphertext cannot be empty")
            
            # Extract optional parameters
            counter_start = kwargs.get('counter_start', 0)
            use_packet_counter = kwargs.get('use_packet_counter', False)
            
            if use_packet_counter:
                return self._decrypt_with_counter(key, ciphertext, counter_start)
            else:
                return self._decrypt_simple(key, ciphertext)
                
        except Exception as e:
            self.logger.error(f"XOR decryption failed: {e}")
            return None
    
    def _decrypt_simple(self, key: bytes, ciphertext: bytes) -> bytes:
        """Simple XOR with repeating key"""
        plaintext = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(ciphertext):
            plaintext.append(byte ^ key[i % key_len])
        
        return bytes(plaintext)
    
    def _decrypt_with_counter(self, key: bytes, ciphertext: bytes, counter_start: int = 0) -> bytes:
        """XOR with incrementing counter (common in packet-based systems)"""
        plaintext = bytearray()
        key_len = len(key)
        counter = counter_start
        
        for i, byte in enumerate(ciphertext):
            # XOR with key byte and counter
            key_byte = key[i % key_len]
            xor_value = key_byte ^ (counter & 0xFF)
            plaintext.append(byte ^ xor_value)
            counter += 1
        
        return bytes(plaintext)
    
    def decrypt_ble_packet_xor(
        self,
        key: bytes,
        encrypted_pdu: bytes,
        packet_counter: Optional[int] = None,
        skip_header: bool = True
    ) -> Optional[bytes]:
        """
        Decrypt a BLE packet using XOR obfuscation.
        
        Args:
            key: XOR key
            encrypted_pdu: Complete encrypted PDU
            packet_counter: Optional packet counter for counter-based XOR
            skip_header: Whether to skip the BLE header (first 3 bytes)
            
        Returns:
            Decrypted payload or None if decryption fails
        """
        try:
            if len(encrypted_pdu) < 3:
                raise BLEDecryptionError("PDU too short for BLE format")
            
            # Skip BLE header if requested (Header + Length = 3 bytes)
            data_start = 3 if skip_header else 0
            payload_to_decrypt = encrypted_pdu[data_start:]
            
            if packet_counter is not None:
                decrypted = self._decrypt_with_counter(key, payload_to_decrypt, packet_counter)
            else:
                decrypted = self._decrypt_simple(key, payload_to_decrypt)
            
            self.logger.debug(f"Successfully XOR decrypted {len(decrypted)} bytes")
            return decrypted
            
        except Exception as e:
            self.logger.error(f"XOR BLE packet decryption failed: {e}")
            return None
    
    def find_xor_key(
        self,
        ciphertext: bytes,
        known_plaintext: bytes,
        key_length: int,
        offset: int = 0
    ) -> Optional[bytes]:
        """
        Find XOR key using known plaintext attack.
        
        Args:
            ciphertext: Encrypted data
            known_plaintext: Known plaintext at specific offset
            key_length: Expected key length
            offset: Offset in ciphertext where known plaintext starts
            
        Returns:
            Recovered XOR key or None if not found
        """
        try:
            if len(ciphertext) < offset + len(known_plaintext):
                raise BLEDecryptionError("Ciphertext too short for known plaintext")
            
            # Extract the portion of ciphertext that corresponds to known plaintext
            cipher_portion = ciphertext[offset:offset + len(known_plaintext)]
            
            # XOR to recover key pattern
            key_pattern = bytearray()
            for i in range(len(known_plaintext)):
                key_pattern.append(cipher_portion[i] ^ known_plaintext[i])
            
            # Extend or truncate to desired key length
            if len(key_pattern) >= key_length:
                recovered_key = bytes(key_pattern[:key_length])
            else:
                # Repeat pattern to fill key length
                recovered_key = bytearray()
                for i in range(key_length):
                    recovered_key.append(key_pattern[i % len(key_pattern)])
                recovered_key = bytes(recovered_key)
            
            self.logger.info(f"Recovered XOR key: {recovered_key.hex()}")
            return recovered_key
            
        except Exception as e:
            self.logger.error(f"XOR key recovery failed: {e}")
            return None
    
    def analyze_xor_patterns(self, ciphertext: bytes, max_key_length: int = 32) -> dict:
        """
        Analyze ciphertext for XOR patterns and potential key lengths.
        
        Args:
            ciphertext: Encrypted data to analyze
            max_key_length: Maximum key length to test
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            'likely_key_lengths': [],
            'byte_frequency': {},
            'pattern_repeats': {},
            'entropy': 0.0
        }
        
        try:
            # Byte frequency analysis
            byte_counts = [0] * 256
            for byte in ciphertext:
                byte_counts[byte] += 1
            
            total_bytes = len(ciphertext)
            for i, count in enumerate(byte_counts):
                if count > 0:
                    results['byte_frequency'][i] = count / total_bytes
            
            # Calculate entropy
            import math
            entropy = 0.0
            for count in byte_counts:
                if count > 0:
                    p = count / total_bytes
                    entropy -= p * math.log2(p)
            results['entropy'] = entropy
            
            # Look for repeating patterns (potential key lengths)
            for key_len in range(1, min(max_key_length + 1, len(ciphertext) // 2)):
                repeats = 0
                for i in range(len(ciphertext) - key_len):
                    if ciphertext[i] == ciphertext[i + key_len]:
                        repeats += 1
                
                repeat_ratio = repeats / (len(ciphertext) - key_len)
                results['pattern_repeats'][key_len] = repeat_ratio
                
                # Key lengths with high repeat ratios are likely
                if repeat_ratio > 0.1:  # Threshold for likely key length
                    results['likely_key_lengths'].append(key_len)
            
            # Sort by likelihood
            results['likely_key_lengths'].sort(
                key=lambda x: results['pattern_repeats'][x], 
                reverse=True
            )
            
        except Exception as e:
            self.logger.error(f"XOR pattern analysis failed: {e}")
        
        return results


# Global instance for convenience functions
_xor_decryptor = BLEXORDecryptor()


def decrypt_ble_packet_xor(
    key: bytes,
    encrypted_pdu: bytes,
    packet_counter: Optional[int] = None,
    skip_header: bool = True
) -> Optional[bytes]:
    """
    Decrypt a BLE packet using XOR obfuscation.
    
    Args:
        key: XOR key
        encrypted_pdu: Complete encrypted PDU
        packet_counter: Optional packet counter for counter-based XOR
        skip_header: Whether to skip the BLE header (first 3 bytes)
        
    Returns:
        Decrypted payload or None if decryption fails
    """
    return _xor_decryptor.decrypt_ble_packet_xor(
        key, encrypted_pdu, packet_counter, skip_header
    )


def find_xor_key_from_known_plaintext(
    ciphertext: bytes,
    known_plaintext: bytes,
    key_length: int,
    offset: int = 0
) -> Optional[bytes]:
    """
    Find XOR key using known plaintext attack.
    
    Args:
        ciphertext: Encrypted data
        known_plaintext: Known plaintext at specific offset
        key_length: Expected key length
        offset: Offset in ciphertext where known plaintext starts
        
    Returns:
        Recovered XOR key or None if not found
    """
    return _xor_decryptor.find_xor_key(ciphertext, known_plaintext, key_length, offset)


def analyze_xor_encryption(ciphertext: bytes, max_key_length: int = 32) -> dict:
    """
    Analyze ciphertext for XOR patterns and potential key lengths.
    
    Args:
        ciphertext: Encrypted data to analyze
        max_key_length: Maximum key length to test
        
    Returns:
        Dictionary with analysis results
    """
    return _xor_decryptor.analyze_xor_patterns(ciphertext, max_key_length)