"""
Tests for BLE XOR Cryptography Utilities
"""

import pytest
from src.utils.ble_crypto import (
    BLEXORDecryptor,
    decrypt_ble_packet_xor,
    find_xor_key_from_known_plaintext,
    analyze_xor_encryption,
    BLEDecryptionError
)


class TestBLEXORDecryptor:
    """Test BLE XOR decryption functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.decryptor = BLEXORDecryptor()
        self.test_key = b"SECRET"
        self.test_plaintext = b"Hello XOR World! This is a test message."
        
    def test_get_algorithm_name(self):
        """Test algorithm name reporting"""
        assert self.decryptor.get_algorithm_name() == "XOR-Obfuscation"
    
    def test_simple_xor_decrypt(self):
        """Test simple XOR decryption with repeating key"""
        # Encrypt manually
        ciphertext = bytearray()
        key_len = len(self.test_key)
        for i, byte in enumerate(self.test_plaintext):
            ciphertext.append(byte ^ self.test_key[i % key_len])
        ciphertext = bytes(ciphertext)
        
        # Decrypt using our function
        result = self.decryptor.decrypt(
            self.test_key,
            b"",  # nonce not used in XOR
            ciphertext,
            None
        )
        
        assert result == self.test_plaintext
    
    def test_counter_xor_decrypt(self):
        """Test XOR decryption with counter"""
        # Encrypt manually with counter
        ciphertext = bytearray()
        key_len = len(self.test_key)
        counter = 42  # Start counter
        
        for i, byte in enumerate(self.test_plaintext):
            key_byte = self.test_key[i % key_len]
            xor_value = key_byte ^ (counter & 0xFF)
            ciphertext.append(byte ^ xor_value)
            counter += 1
        
        ciphertext = bytes(ciphertext)
        
        # Decrypt using our function
        result = self.decryptor.decrypt(
            self.test_key,
            b"",  # nonce not used in XOR
            ciphertext,
            None,
            counter_start=42,
            use_packet_counter=True
        )
        
        assert result == self.test_plaintext
    
    def test_empty_key_error(self):
        """Test that empty key raises error"""
        with pytest.raises(BLEDecryptionError, match="XOR key cannot be empty"):
            self.decryptor.decrypt(b"", b"", b"test", None)
    
    def test_empty_ciphertext_error(self):
        """Test that empty ciphertext raises error"""
        with pytest.raises(BLEDecryptionError, match="Ciphertext cannot be empty"):
            self.decryptor.decrypt(b"key", b"", b"", None)
    
    def test_decrypt_ble_packet_xor_skip_header(self):
        """Test BLE packet XOR decryption skipping header"""
        # Create fake BLE packet: Header(1) + Length(2) + Payload
        header = b"\x02"
        length = len(self.test_plaintext).to_bytes(2, 'little')
        
        # XOR encrypt the payload
        payload_encrypted = bytearray()
        key_len = len(self.test_key)
        for i, byte in enumerate(self.test_plaintext):
            payload_encrypted.append(byte ^ self.test_key[i % key_len])
        
        full_pdu = header + length + bytes(payload_encrypted)
        
        # Decrypt
        result = self.decryptor.decrypt_ble_packet_xor(
            self.test_key,
            full_pdu,
            skip_header=True
        )
        
        assert result == self.test_plaintext
    
    def test_decrypt_ble_packet_xor_with_counter(self):
        """Test BLE packet XOR decryption with packet counter"""
        header = b"\x02"
        length = len(self.test_plaintext).to_bytes(2, 'little')
        
        # XOR encrypt with counter
        payload_encrypted = bytearray()
        key_len = len(self.test_key)
        counter = 100
        
        for i, byte in enumerate(self.test_plaintext):
            key_byte = self.test_key[i % key_len]
            xor_value = key_byte ^ (counter & 0xFF)
            payload_encrypted.append(byte ^ xor_value)
            counter += 1
        
        full_pdu = header + length + bytes(payload_encrypted)
        
        # Decrypt
        result = self.decryptor.decrypt_ble_packet_xor(
            self.test_key,
            full_pdu,
            packet_counter=100,
            skip_header=True
        )
        
        assert result == self.test_plaintext
    
    def test_pdu_too_short_error(self):
        """Test error when PDU is too short"""
        short_pdu = b"\x02"  # Only 1 byte
        
        result = self.decryptor.decrypt_ble_packet_xor(
            self.test_key,
            short_pdu
        )
        
        assert result is None
    
    def test_find_xor_key_known_plaintext(self):
        """Test XOR key recovery using known plaintext"""
        known_plain = b"HELLO"
        key_to_find = b"KEY123"
        
        # Create ciphertext with known plaintext at offset 5
        dummy_prefix = b"DUMMY"
        plaintext = dummy_prefix + known_plain + b"MORE DATA"
        
        # Encrypt
        ciphertext = bytearray()
        key_len = len(key_to_find)
        for i, byte in enumerate(plaintext):
            ciphertext.append(byte ^ key_to_find[i % key_len])
        
        # Recover key
        recovered_key = self.decryptor.find_xor_key(
            bytes(ciphertext),
            known_plain,
            len(key_to_find),
            offset=5
        )
        
        assert recovered_key == key_to_find
    
    def test_find_xor_key_pattern_repeat(self):
        """Test key recovery when known plaintext is shorter than key"""
        known_plain = b"HI"
        key_to_find = b"LONGKEY"
        
        # Create ciphertext
        ciphertext = bytearray()
        key_len = len(key_to_find)
        for i, byte in enumerate(known_plain):
            ciphertext.append(byte ^ key_to_find[i % key_len])
        
        # Recover key (should repeat pattern)
        recovered_key = self.decryptor.find_xor_key(
            bytes(ciphertext),
            known_plain,
            len(key_to_find),
            offset=0
        )
        
        # Should be "HIHIHIH" (pattern repeated)
        expected = b"HIHIHIH"
        assert recovered_key == expected
    
    def test_analyze_xor_patterns(self):
        """Test XOR pattern analysis"""
        # Create data with repeating 4-byte key
        key = b"ABCD"
        plaintext = b"This is a test message for pattern analysis" * 3
        
        # Encrypt
        ciphertext = bytearray()
        for i, byte in enumerate(plaintext):
            ciphertext.append(byte ^ key[i % len(key)])
        
        # Analyze
        analysis = self.decryptor.analyze_xor_patterns(bytes(ciphertext), max_key_length=10)
        
        # Check that key length 4 is detected as likely
        assert 4 in analysis['likely_key_lengths']
        assert len(analysis['byte_frequency']) > 0
        assert analysis['entropy'] > 0
        assert 4 in analysis['pattern_repeats']
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        # Test decrypt_ble_packet_xor
        header = b"\x02"
        length = len(self.test_plaintext).to_bytes(2, 'little')
        
        payload_encrypted = bytearray()
        key_len = len(self.test_key)
        for i, byte in enumerate(self.test_plaintext):
            payload_encrypted.append(byte ^ self.test_key[i % key_len])
        
        full_pdu = header + length + bytes(payload_encrypted)
        
        result = decrypt_ble_packet_xor(self.test_key, full_pdu)
        assert result == self.test_plaintext
        
        # Test find_xor_key_from_known_plaintext
        known_plain = b"TEST"
        key_to_find = b"MYKEY"
        
        ciphertext = bytearray()
        for i, byte in enumerate(known_plain):
            ciphertext.append(byte ^ key_to_find[i % len(key_to_find)])
        
        recovered = find_xor_key_from_known_plaintext(
            bytes(ciphertext), known_plain, len(key_to_find)
        )
        assert recovered == key_to_find
        
        # Test analyze_xor_encryption
        analysis = analyze_xor_encryption(bytes(ciphertext))
        assert 'likely_key_lengths' in analysis
        assert 'byte_frequency' in analysis
        assert 'entropy' in analysis
    
    def test_single_byte_key(self):
        """Test XOR with single byte key"""
        key = b"\x42"
        plaintext = b"Single byte XOR test"
        
        # Encrypt
        ciphertext = bytes(byte ^ key[0] for byte in plaintext)
        
        # Decrypt
        result = self.decryptor.decrypt(key, b"", ciphertext, None)
        assert result == plaintext
    
    def test_key_longer_than_plaintext(self):
        """Test XOR with key longer than plaintext"""
        key = b"VERYLONGKEYFORTESTING"
        plaintext = b"SHORT"
        
        # Encrypt
        ciphertext = bytes(plaintext[i] ^ key[i] for i in range(len(plaintext)))
        
        # Decrypt
        result = self.decryptor.decrypt(key, b"", ciphertext, None)
        assert result == plaintext