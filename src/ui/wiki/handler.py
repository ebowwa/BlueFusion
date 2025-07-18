#!/usr/bin/env python3
"""
BlueFusion Wiki Handler
Main handler that coordinates content loading and searching
"""

try:
    # Try relative imports first (when used as a module)
    from .content_loader import ContentLoader
    from .search import WikiSearch
except ImportError:
    # Fall back to absolute imports (when run directly)
    from content_loader import ContentLoader
    from search import WikiSearch

class WikiHandler:
    """Handles wiki content management and retrieval"""
    
    def __init__(self):
        self.content_loader = ContentLoader()
        self.search_engine = WikiSearch(self.content_loader)
    
    def get_topics(self):
        """Get list of available wiki topics"""
        return self.content_loader.get_topics()
    
    def get_content(self, topic: str) -> str:
        """Get content for a specific topic"""
        return self.content_loader.get_content(topic)
    
    def search_content(self, query: str) -> str:
        """Search for content across all topics"""
        return self.search_engine.search_content(query)