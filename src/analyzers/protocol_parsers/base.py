"""
Base Protocol Parser
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ParsedField(BaseModel):
    """Represents a parsed protocol field"""
    name: str
    value: Any
    offset: int
    size: int
    description: str = ""
    
    
class ProtocolParser(ABC):
    """Base class for all protocol parsers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def parse(self, data: bytes) -> Dict[str, Any]:
        """
        Parse raw packet data
        
        Args:
            data: Raw packet bytes
            
        Returns:
            Dictionary containing parsed fields
        """
        pass
    
    @abstractmethod
    def can_parse(self, data: bytes) -> bool:
        """
        Check if this parser can handle the given data
        
        Args:
            data: Raw packet bytes
            
        Returns:
            True if parser can handle this data
        """
        pass
    
    def parse_fields(self, data: bytes) -> List[ParsedField]:
        """
        Parse data into structured fields
        
        Args:
            data: Raw packet bytes
            
        Returns:
            List of parsed fields
        """
        return []
    
    @staticmethod
    def format_value(value: Any) -> str:
        """Format value for display"""
        if isinstance(value, bytes):
            return value.hex()
        elif isinstance(value, int):
            return f"0x{value:02X} ({value})"
        else:
            return str(value)