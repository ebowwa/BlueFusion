"""
BLE Security Manager
Centralized security handling for all BLE interfaces
"""
from typing import Optional, Dict, Any, Callable, Awaitable, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import os
from pathlib import Path

from ..utils.ble_crypto import (
    BLEAESCCMDecryptor, BLEXORDecryptor, 
    decrypt_ble_packet_aes_ccm, decrypt_ble_packet_xor,
    find_xor_key_from_known_plaintext, analyze_xor_encryption
)


class SecurityLevel(Enum):
    """BLE Security Levels"""
    NO_SECURITY = 0
    UNAUTHENTICATED_ENCRYPTION = 1
    AUTHENTICATED_ENCRYPTION = 2
    AUTHENTICATED_LE_SECURE_CONNECTIONS = 3


class PairingMethod(Enum):
    """BLE Pairing Methods"""
    JUST_WORKS = "just_works"
    PASSKEY_ENTRY = "passkey_entry"
    NUMERIC_COMPARISON = "numeric_comparison"
    OUT_OF_BAND = "out_of_band"


@dataclass
class SecurityRequirements:
    """Security requirements for a BLE operation"""
    min_security_level: SecurityLevel = SecurityLevel.NO_SECURITY
    require_bonding: bool = False
    require_mitm: bool = False  # Man-in-the-middle protection
    require_secure_connections: bool = False


@dataclass
class BondInfo:
    """Stored bond information for a device"""
    address: str
    ltk: Optional[bytes] = None  # Long Term Key
    irk: Optional[bytes] = None  # Identity Resolving Key
    csrk: Optional[bytes] = None  # Connection Signature Resolving Key
    security_level: SecurityLevel = SecurityLevel.NO_SECURITY
    authenticated: bool = False
    # Decryption keys for weak encryption
    xor_key: Optional[bytes] = None
    custom_key: Optional[bytes] = None


class SecurityManager:
    """Manages BLE security operations across all interfaces"""
    
    def __init__(self, bond_storage_path: Optional[Path] = None):
        self.bond_storage_path = bond_storage_path or Path.home() / ".bluefusion" / "bonds.json"
        self.bonds: Dict[str, BondInfo] = {}
        self._pairing_callbacks: Dict[str, Callable] = {}
        # Initialize decryptors
        self.aes_ccm_decryptor = BLEAESCCMDecryptor()
        self.xor_decryptor = BLEXORDecryptor()
        self._load_bonds()
    
    def _load_bonds(self):
        """Load stored bonds from disk"""
        if self.bond_storage_path.exists():
            try:
                with open(self.bond_storage_path, 'r') as f:
                    data = json.load(f)
                    for addr, bond_data in data.items():
                        self.bonds[addr] = BondInfo(
                            address=addr,
                            security_level=SecurityLevel(bond_data.get('security_level', 0)),
                            authenticated=bond_data.get('authenticated', False)
                        )
            except Exception as e:
                print(f"Failed to load bonds: {e}")
    
    def _save_bonds(self):
        """Save bonds to disk"""
        try:
            self.bond_storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for addr, bond in self.bonds.items():
                data[addr] = {
                    'security_level': bond.security_level.value,
                    'authenticated': bond.authenticated
                }
            with open(self.bond_storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save bonds: {e}")
    
    def register_pairing_callback(self, callback_type: str, 
                                callback: Callable[[str, Any], Awaitable[Any]]):
        """Register callback for pairing events"""
        self._pairing_callbacks[callback_type] = callback
    
    async def request_pairing(self, device_address: str, 
                            method: PairingMethod = PairingMethod.JUST_WORKS) -> bool:
        """Initiate pairing with a device"""
        if method == PairingMethod.PASSKEY_ENTRY:
            if 'passkey_request' in self._pairing_callbacks:
                passkey = await self._pairing_callbacks['passkey_request'](
                    device_address, "Enter 6-digit passkey"
                )
                return await self._perform_passkey_pairing(device_address, passkey)
        
        elif method == PairingMethod.NUMERIC_COMPARISON:
            if 'numeric_comparison' in self._pairing_callbacks:
                confirmed = await self._pairing_callbacks['numeric_comparison'](
                    device_address, "123456"  # Example code
                )
                return confirmed
        
        # For JUST_WORKS, no user interaction needed
        return True
    
    async def _perform_passkey_pairing(self, device_address: str, passkey: str) -> bool:
        """Perform passkey pairing (implementation depends on platform)"""
        # This would be implemented by the specific interface (MacBook BLE, etc.)
        # For now, we'll simulate success
        await asyncio.sleep(1)  # Simulate pairing delay
        
        # Store bond info
        self.bonds[device_address] = BondInfo(
            address=device_address,
            security_level=SecurityLevel.AUTHENTICATED_ENCRYPTION,
            authenticated=True
        )
        self._save_bonds()
        return True
    
    def check_security_requirements(self, device_address: str, 
                                  requirements: SecurityRequirements) -> bool:
        """Check if current security meets requirements"""
        bond = self.bonds.get(device_address)
        if not bond:
            return requirements.min_security_level == SecurityLevel.NO_SECURITY
        
        return bond.security_level.value >= requirements.min_security_level.value
    
    def get_bond_info(self, device_address: str) -> Optional[BondInfo]:
        """Get bond information for a device"""
        return self.bonds.get(device_address)
    
    def remove_bond(self, device_address: str) -> bool:
        """Remove bond with a device"""
        if device_address in self.bonds:
            del self.bonds[device_address]
            self._save_bonds()
            return True
        return False
    
    def is_bonded(self, device_address: str) -> bool:
        """Check if device is bonded"""
        return device_address in self.bonds
    
    async def handle_security_request(self, device_address: str, 
                                    security_level: SecurityLevel) -> bool:
        """Handle incoming security request from device"""
        current_bond = self.bonds.get(device_address)
        
        if not current_bond or current_bond.security_level.value < security_level.value:
            # Need to pair/re-pair
            method = self._determine_pairing_method(device_address)
            return await self.request_pairing(device_address, method)
        
        return True
    
    def _determine_pairing_method(self, device_address: str) -> PairingMethod:
        """Determine appropriate pairing method for device"""
        # This could be enhanced to check device capabilities
        # For now, default to passkey entry for better security
        return PairingMethod.PASSKEY_ENTRY
    
    # Decryption methods
    def decrypt_packet(self, device_address: str, encrypted_pdu: bytes, 
                      packet_counter: Optional[int] = None) -> Optional[bytes]:
        """
        Attempt to decrypt a BLE packet using available keys/methods
        
        Args:
            device_address: Device address
            encrypted_pdu: Encrypted PDU data
            packet_counter: Optional packet counter for algorithms that need it
            
        Returns:
            Decrypted data or None if decryption fails
        """
        bond = self.bonds.get(device_address)
        if not bond:
            return None
        
        # Try AES-CCM if we have LTK
        if bond.ltk:
            try:
                # For AES-CCM, we'd need the proper IV/nonce construction
                # This is a simplified example
                result = self._try_aes_ccm_decrypt(bond, encrypted_pdu, packet_counter)
                if result:
                    return result
            except Exception:
                pass
        
        # Try XOR if we have XOR key
        if bond.xor_key:
            try:
                result = decrypt_ble_packet_xor(
                    bond.xor_key, encrypted_pdu, packet_counter
                )
                if result:
                    return result
            except Exception:
                pass
        
        return None
    
    def _try_aes_ccm_decrypt(self, bond: BondInfo, encrypted_pdu: bytes, 
                           packet_counter: Optional[int]) -> Optional[bytes]:
        """Try AES-CCM decryption with bond information"""
        if not bond.ltk or not packet_counter:
            return None
        
        # This would require proper IV construction from bond info
        # For demonstration, we'll skip the full implementation
        return None
    
    def set_xor_key(self, device_address: str, xor_key: bytes):
        """Set XOR key for a device"""
        if device_address not in self.bonds:
            self.bonds[device_address] = BondInfo(address=device_address)
        
        self.bonds[device_address].xor_key = xor_key
        self._save_bonds()
    
    def analyze_encrypted_traffic(self, device_address: str, 
                                encrypted_packets: List[bytes]) -> Dict[str, Any]:
        """
        Analyze encrypted traffic to determine encryption method and potential keys
        
        Args:
            device_address: Device address
            encrypted_packets: List of encrypted packet data
            
        Returns:
            Analysis results with recommendations
        """
        if not encrypted_packets:
            return {"error": "No packets to analyze"}
        
        results = {
            "device_address": device_address,
            "packet_count": len(encrypted_packets),
            "analysis": {}
        }
        
        # Analyze for XOR patterns
        combined_data = b"".join(encrypted_packets)
        xor_analysis = analyze_xor_encryption(combined_data)
        results["analysis"]["xor"] = xor_analysis
        
        # Check for potential AES-CCM (fixed packet structure, entropy)
        aes_indicators = self._analyze_for_aes_ccm(encrypted_packets)
        results["analysis"]["aes_ccm"] = aes_indicators
        
        # Generate recommendations
        recommendations = []
        if xor_analysis["likely_key_lengths"]:
            recommendations.append({
                "method": "XOR",
                "confidence": "medium",
                "key_lengths": xor_analysis["likely_key_lengths"][:3],
                "action": "Try XOR decryption with suggested key lengths"
            })
        
        if aes_indicators["likely_aes_ccm"]:
            recommendations.append({
                "method": "AES-CCM",
                "confidence": "high",
                "action": "Standard BLE encryption - need proper pairing"
            })
        
        results["recommendations"] = recommendations
        return results
    
    def _analyze_for_aes_ccm(self, packets: List[bytes]) -> Dict[str, Any]:
        """Analyze packets for AES-CCM indicators"""
        results = {
            "likely_aes_ccm": False,
            "consistent_structure": False,
            "high_entropy": False
        }
        
        if not packets:
            return results
        
        # Check for consistent packet structure (BLE header pattern)
        header_consistency = 0
        for packet in packets:
            if len(packet) >= 3:
                # Check if looks like BLE header
                if packet[0] & 0x03 in [0x01, 0x02, 0x03]:  # Valid BLE PDU types
                    header_consistency += 1
        
        if header_consistency / len(packets) > 0.8:
            results["consistent_structure"] = True
        
        # Check entropy of payloads (AES-CCM should have high entropy)
        total_entropy = 0
        for packet in packets:
            if len(packet) > 7:  # Skip header, analyze payload
                payload = packet[7:]
                entropy = self._calculate_entropy(payload)
                total_entropy += entropy
        
        avg_entropy = total_entropy / len(packets) if packets else 0
        if avg_entropy > 7.0:  # High entropy suggests strong encryption
            results["high_entropy"] = True
        
        results["likely_aes_ccm"] = (
            results["consistent_structure"] and results["high_entropy"]
        )
        
        return results
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        import math
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        entropy = 0.0
        total = len(data)
        for count in byte_counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def attempt_xor_key_recovery(self, device_address: str, 
                               encrypted_packet: bytes, 
                               known_plaintext: bytes,
                               plaintext_offset: int = 0) -> Optional[bytes]:
        """
        Attempt to recover XOR key using known plaintext
        
        Args:
            device_address: Device address
            encrypted_packet: Single encrypted packet
            known_plaintext: Known plaintext content
            plaintext_offset: Offset in packet where plaintext starts
            
        Returns:
            Recovered XOR key or None
        """
        # Try different key lengths
        for key_length in [1, 2, 4, 8, 16, 32]:
            try:
                recovered_key = find_xor_key_from_known_plaintext(
                    encrypted_packet, known_plaintext, key_length, plaintext_offset
                )
                
                if recovered_key:
                    # Test the key by trying to decrypt
                    test_decrypt = decrypt_ble_packet_xor(
                        recovered_key, encrypted_packet
                    )
                    
                    if test_decrypt and known_plaintext in test_decrypt:
                        # Key works! Store it
                        self.set_xor_key(device_address, recovered_key)
                        return recovered_key
                        
            except Exception:
                continue
        
        return None