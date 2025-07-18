#!/usr/bin/env python3
"""
Wiki Content Loader
Loads wiki content from individual module files
"""

class ContentLoader:
    """Loads wiki content from modular files"""
    
    def __init__(self):
        self._content_cache = {}
        self._load_content()
    
    def _load_content(self):
        """Load content from all wiki modules"""
        try:
            # Try relative imports first (when used as a module)
            from .getting_started import CONTENT as getting_started_content
            from .ble_basics import CONTENT as ble_basics_content
            from .interface_configuration import CONTENT as interface_configuration_content
            from .troubleshooting import CONTENT as troubleshooting_content
            from .api_reference import CONTENT as api_reference_content
            from .architecture import CONTENT as architecture_content
            from .api_examples import CONTENT as api_examples_content
            from .deployment_guide import CONTENT as deployment_guide_content
            from .packet_analysis import CONTENT as packet_analysis_content
            from .security_guide import CONTENT as security_guide_content
            from .advanced_features import CONTENT as advanced_features_content
            from .ble_hacking_overview import CONTENT as ble_hacking_overview_content
            from .ble_traffic_capture import CONTENT as ble_traffic_capture_content
            from .ble_tools_comparison import CONTENT as ble_tools_comparison_content
            from .ble_hacking_examples import CONTENT as ble_hacking_examples_content
            from .influences import CONTENT as influences_content
        except ImportError:
            # Fall back to absolute imports (when run directly)
            from getting_started import CONTENT as getting_started_content
            from ble_basics import CONTENT as ble_basics_content
            from interface_configuration import CONTENT as interface_configuration_content
            from troubleshooting import CONTENT as troubleshooting_content
            from api_reference import CONTENT as api_reference_content
            from architecture import CONTENT as architecture_content
            from api_examples import CONTENT as api_examples_content
            from deployment_guide import CONTENT as deployment_guide_content
            from packet_analysis import CONTENT as packet_analysis_content
            from security_guide import CONTENT as security_guide_content
            from advanced_features import CONTENT as advanced_features_content
            from ble_hacking_overview import CONTENT as ble_hacking_overview_content
            from ble_traffic_capture import CONTENT as ble_traffic_capture_content
            from ble_tools_comparison import CONTENT as ble_tools_comparison_content
            from ble_hacking_examples import CONTENT as ble_hacking_examples_content
            from influences import CONTENT as influences_content
        
        self._content_cache = {
            "Getting Started": getting_started_content,
            "BLE Basics": ble_basics_content,
            "Interface Configuration": interface_configuration_content,
            "Technical Architecture": architecture_content,
            "API Examples": api_examples_content,
            "API Reference": api_reference_content,
            "Packet Analysis": packet_analysis_content,
            "Security Guide": security_guide_content,
            "BLE Hacking Overview": ble_hacking_overview_content,
            "BLE Traffic Capture": ble_traffic_capture_content,
            "BLE Tools Comparison": ble_tools_comparison_content,
            "BLE Hacking Examples": ble_hacking_examples_content,
            "Advanced Features": advanced_features_content,
            "Deployment Guide": deployment_guide_content,
            "Troubleshooting": troubleshooting_content,
            "Influences": influences_content
        }
    
    def get_all_content(self):
        """Get all wiki content"""
        return self._content_cache.copy()
    
    def get_content(self, topic: str) -> str:
        """Get content for a specific topic"""
        return self._content_cache.get(topic, "Topic not found")
    
    def get_topics(self):
        """Get list of available topics"""
        return list(self._content_cache.keys())