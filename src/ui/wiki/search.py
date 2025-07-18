#!/usr/bin/env python3
"""
Wiki Search Module
Handles searching across wiki content
"""

class WikiSearch:
    """Handles searching across wiki content"""
    
    def __init__(self, content_loader):
        self.content_loader = content_loader
    
    def search_content(self, query: str) -> str:
        """Search for content across all topics"""
        results = []
        query_lower = query.lower()
        
        for topic, content in self.content_loader.get_all_content().items():
            if query_lower in content.lower():
                # Find the line containing the query
                lines = content.split('\n')
                matching_lines = [line for line in lines if query_lower in line.lower()]
                if matching_lines:
                    results.append(f"**{topic}**:\n" + "\n".join(matching_lines[:3]))
        
        if results:
            return "## Search Results\n\n" + "\n\n".join(results)
        else:
            return f"No results found for '{query}'"