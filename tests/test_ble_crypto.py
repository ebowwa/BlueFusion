"""
Tests for BLE AES-CCM Cryptography Utilities
"""

import pytest
from src.utils.ble_crypto import (
    BLEAESCCMDecryptor,
    decrypt_ble_packet_aes_ccm,
    decrypt_ble_data_channel_aes_ccm,
    BLEDecryptionError
)


class TestBLEAESCCMDecryptor:
    """Test BLE AES-CCM decryption functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.decryptor = BLEAESCCMDecryptor()
        
        # Test vectors from Bluetooth Core Spec v5.3, Vol 6, Part C, Section 1
        self.test_key = bytes.fromhex("89678967896789678967896789678967")  # 128-bit key
        self.test_iv = bytes.fromhex("1234567890abcdef")  # 8-byte IV
        self.test_plaintext = b"Hello BLE World!"
        
    def test_get_algorithm_name(self):
        """Test algorithm name reporting"""
        assert self.decryptor.get_algorithm_name() == "AES-CCM"
        
    def test_aes_ccm_decrypt_valid(self):
        """Test successful AES-CCM decryption"""
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
        
        cipher = AESCCM(self.test_key, tag_length=4)
        nonce = self.test_iv + b"\x00\x00\x00\x00\x00"  # 13-byte nonce
        aad = b"\x02\x10\x00"  # Sample BLE header
        
        ciphertext = cipher.encrypt(nonce, self.test_plaintext, aad)
        
        # Test decryption
        result = self.decryptor.decrypt(
            self.test_key,
            nonce,
            ciphertext,
            aad,
            tag_length=4
        )
        
        assert result == self.test_plaintext
    
    def test_aes_ccm_decrypt_invalid_tag(self):
        """Test AES-CCM decryption with invalid authentication tag"""
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
        
        cipher = AESCCM(self.test_key, tag_length=4)
        nonce = self.test_iv + b"\x00\x00\x00\x00\x00"
        aad = b"\x02\x10\x00"
        
        ciphertext = cipher.encrypt(nonce, self.test_plaintext, aad)
        
        # Corrupt the tag (last 4 bytes)
        corrupted = ciphertext[:-4] + b"\x00\x00\x00\x00"
        
        result = self.decryptor.decrypt(
            self.test_key,
            nonce,
            corrupted,
            aad,
            tag_length=4
        )
        
        assert result is None
    
    def test_construct_ble_nonce_master_to_slave(self):
        """Test BLE nonce construction for master to slave direction"""
        iv = bytes.fromhex("1234567890abcdef")
        packet_counter = 0x123456
        
        nonce = self.decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave=True)
        
        assert len(nonce) == 13
        assert nonce[:8] == iv
        # Check direction bit is set (MSB of counter)
        assert (nonce[12] & 0x80) == 0x80
    
    def test_construct_ble_nonce_slave_to_master(self):
        """Test BLE nonce construction for slave to master direction"""
        iv = bytes.fromhex("1234567890abcdef")
        packet_counter = 0x123456
        
        nonce = self.decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave=False)
        
        assert len(nonce) == 13
        assert nonce[:8] == iv
        # Check direction bit is not set
        assert (nonce[12] & 0x80) == 0x00
    
    def test_parse_encrypted_pdu_valid(self):
        """Test parsing of valid encrypted PDU"""
        # Construct a sample PDU: Header(1) + Length(2) + Payload + MIC(4)
        header = b"\x02"  # Data PDU
        length = b"\x10\x00"  # 16 bytes payload
        payload = b"A" * 16
        mic = b"\x11\x22\x33\x44"
        
        pdu = header + length + payload + mic
        
        h, p, m = self.decryptor.parse_encrypted_pdu(pdu, tag_length=4)
        
        assert h == header
        assert p == payload
        assert m == mic
    
    def test_parse_encrypted_pdu_too_short(self):
        """Test parsing of PDU that's too short"""
        pdu = b"\x02\x03"  # Only header and partial length
        
        h, p, m = self.decryptor.parse_encrypted_pdu(pdu, tag_length=4)
        
        assert h is None
        assert p is None
        assert m is None
    
    def test_decrypt_ble_packet_aes_ccm_integration(self):
        """Test full BLE packet decryption with AES-CCM"""
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
        
        key = bytes.fromhex("89678967896789678967896789678967")
        iv = bytes.fromhex("1234567890abcdef")
        packet_counter = 1
        plaintext = b"Test BLE data"
        
        # Construct nonce
        nonce = self.decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave=True)
        
        # Create PDU header
        header = b"\x02"  # Data PDU
        length = len(plaintext).to_bytes(2, 'little')
        aad = header + length
        
        # Encrypt
        cipher = AESCCM(key, tag_length=4)
        ciphertext_with_tag = cipher.encrypt(nonce, plaintext, aad)
        
        # Construct full PDU
        encrypted_pdu = header + length + ciphertext_with_tag
        
        # Decrypt using convenience function
        result = decrypt_ble_packet_aes_ccm(
            key, iv, packet_counter, encrypted_pdu,
            is_master_to_slave=True, tag_length=4
        )
        
        assert result == plaintext
    
    def test_decrypt_ble_data_channel_aes_ccm(self):
        """Test BLE data channel decryption with AES-CCM"""
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
        
        ltk = bytes.fromhex("89678967896789678967896789678967")
        skd_master = bytes.fromhex("12345678")
        skd_slave = bytes.fromhex("90abcdef")
        packet_counter = 42
        plaintext = b"Data channel test"
        
        # Construct IV and nonce as the function would
        iv = skd_slave + skd_master
        nonce = self.decryptor.construct_ble_nonce(iv, packet_counter, is_master_to_slave=True)
        
        # Encrypt
        cipher = AESCCM(ltk, tag_length=4)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        # Decrypt using convenience function
        result = decrypt_ble_data_channel_aes_ccm(
            ltk, skd_master, skd_slave, ciphertext, packet_counter, is_master_to_slave=True
        )
        
        assert result == plaintext
    
    def test_invalid_key_length(self):
        """Test that invalid key lengths raise BLEDecryptionError"""
        with pytest.raises(BLEDecryptionError, match="Key must be 16 bytes"):
            self.decryptor.decrypt(
                b"short_key",
                b"\x00" * 13,
                b"ciphertext",
                None,
                4
            )
    
    def test_invalid_nonce_length(self):
        """Test that invalid nonce lengths raise BLEDecryptionError"""
        with pytest.raises(BLEDecryptionError, match="Nonce must be 13 bytes"):
            self.decryptor.decrypt(
                b"\x00" * 16,
                b"\x00" * 10,  # Wrong length
                b"ciphertext",
                None,
                4
            )
    
    def test_invalid_tag_length(self):
        """Test that invalid tag lengths raise BLEDecryptionError"""
        with pytest.raises(BLEDecryptionError, match="Invalid tag length"):
            self.decryptor.decrypt(
                b"\x00" * 16,
                b"\x00" * 13,
                b"ciphertext",
                None,
                5  # Invalid tag length
            )
    
    def test_invalid_iv_length_in_nonce_construction(self):
        """Test invalid IV length in nonce construction"""
        with pytest.raises(BLEDecryptionError, match="IV must be 8 bytes"):
            self.decryptor.construct_ble_nonce(
                b"\x00" * 6,  # Wrong length
                123,
                True
            )
    
    def test_packet_counter_too_large(self):
        """Test packet counter that's too large"""
        with pytest.raises(BLEDecryptionError, match="Packet counter too large"):
            self.decryptor.construct_ble_nonce(
                b"\x00" * 8,
                1 << 40,  # Too large
                True
            )