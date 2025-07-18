"""
Simplified Roadmap UI with better interaction
"""
import gradio as gr
from typing import List, Tuple, Dict, Optional
try:
    from .roadmap_tracker import ROADMAP_FEATURES, get_feature_stats
    from .roadmap_storage import RoadmapStorage
except ImportError:
    from roadmap_tracker import ROADMAP_FEATURES, get_feature_stats
    from roadmap_storage import RoadmapStorage

class SimplifiedRoadmapUI:
    def __init__(self):
        self.storage = RoadmapStorage()
        self.features = self.storage.merge_with_defaults(ROADMAP_FEATURES.copy())
        self.selected_feature = None
        self.selected_category = None
        
    def get_categories_with_counts(self) -> List[str]:
        """Get categories with pending counts"""
        categories = []
        for cat, features in self.features.items():
            pending = sum(1 for f in features.values() if f['status'] == 'pending')
            total = len(features)
            categories.append(f"{cat} ({pending}/{total} pending)")
        return categories
    
    def format_feature_list(self, category: str) -> List[List[str]]:
        """Format features as clickable list with checkboxes"""
        if ' (' in category:  # Remove count from category name
            category = category.split(' (')[0]
            
        features = self.features.get(category, {})
        rows = []
        
        for idx, (feature, info) in enumerate(features.items()):
            status_emoji = {
                'completed': '✅',
                'partial': '🔶',
                'pending': '⬜'
            }.get(info['status'], '❓')
            
            # Make row clickable by including index
            rows.append([
                idx,  # Index for selection
                f"{status_emoji} {feature}",
                info['description'],
                info['status']
            ])
        
        return rows
    
    def select_feature(self, category: str, selected_rows: List[int]) -> Tuple[str, str, str]:
        """Handle feature selection and generate instant context"""
        if ' (' in category:
            category = category.split(' (')[0]
        
        if not selected_rows:
            return "No feature selected", "", "Select a feature from the table above"
        
        # Get the selected feature
        features_list = list(self.features[category].items())
        if selected_rows[0] < len(features_list):
            feature_name, feature_info = features_list[selected_rows[0]]
            self.selected_feature = feature_name
            self.selected_category = category
            
            # Generate instant context
            quick_context = f"Feature: {feature_name}\nCategory: {category}\nStatus: {feature_info['status']}\nDescription: {feature_info['description']}"
            
            # Generate copy text
            copy_text = f"I need to implement the '{feature_name}' feature for BlueFusion. {feature_info['description']}"
            
            # Status update
            status = f"Selected: {feature_name}"
            
            return status, quick_context, copy_text
        
        return "Invalid selection", "", ""
    
    def update_feature_status(self, new_status: str, notes: str) -> Tuple[str, List[List[str]]]:
        """Quick update of selected feature status"""
        if not self.selected_feature or not self.selected_category:
            return "No feature selected", []
        
        # Update in memory
        self.features[self.selected_category][self.selected_feature]['status'] = new_status
        if notes:
            self.features[self.selected_category][self.selected_feature]['notes'] = notes
        
        # Save to storage
        self.storage.update_feature_status(self.selected_category, self.selected_feature, new_status, notes)
        
        # Return updated table
        return f"✅ Updated {self.selected_feature} to {new_status}", self.format_feature_list(self.selected_category)
    
    def search_all_features(self, query: str) -> List[List[str]]:
        """Simple search across all features"""
        if not query.strip():
            return []
        
        query = query.lower()
        results = []
        
        for category, features in self.features.items():
            for feature, info in features.items():
                if (query in feature.lower() or 
                    query in info['description'].lower()):
                    
                    status_emoji = {
                        'completed': '✅',
                        'partial': '🔶', 
                        'pending': '⬜'
                    }.get(info['status'], '❓')
                    
                    results.append([
                        f"{status_emoji} {feature}",
                        category,
                        info['description']
                    ])
        
        return results[:20]  # Limit to 20 results
    
    def get_quick_stats(self) -> str:
        """Get simple stats display"""
        stats = get_feature_stats()
        return f"""**Progress: {stats['completion_percentage']}%**
✅ Completed: {stats['completed']}
🔶 Partial: {stats['partial']}
⬜ Pending: {stats['pending']}
Total: {stats['total']} features"""
    
    def generate_batch_context(self, category: str) -> str:
        """Generate context for all pending features in category"""
        if ' (' in category:
            category = category.split(' (')[0]
            
        features = self.features.get(category, {})
        pending = [(f, info) for f, info in features.items() if info['status'] == 'pending']
        
        if not pending:
            return "No pending features in this category!"
        
        context = f"Implement these {len(pending)} pending features in {category}:\n\n"
        for feature, info in pending[:10]:  # Limit to first 10
            context += f"• {feature}: {info['description']}\n"
        
        if len(pending) > 10:
            context += f"\n... and {len(pending) - 10} more features"
        
        return context