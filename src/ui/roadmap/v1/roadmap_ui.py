"""
Roadmap TODO UI component for BlueFusion
"""
import gradio as gr
from typing import List, Tuple, Dict, Set
from .roadmap_tracker import ROADMAP_FEATURES, get_feature_stats, update_feature_status
from .roadmap_storage import RoadmapStorage
import json

class RoadmapUI:
    def __init__(self):
        self.storage = RoadmapStorage()
        # Load saved status and merge with defaults
        self.features = self.storage.merge_with_defaults(ROADMAP_FEATURES.copy())
        # Track selected features for batch operations
        self.selected_features = set()
        
    def get_category_progress(self, category: str) -> str:
        """Get progress bar for a category"""
        features = self.features.get(category, {})
        total = len(features)
        if total == 0:
            return "No features"
        
        completed = sum(1 for f in features.values() if f['status'] == 'completed')
        partial = sum(1 for f in features.values() if f['status'] == 'partial')
        
        percentage = ((completed + partial * 0.5) / total) * 100
        return f"{completed}/{total} completed ({percentage:.0f}%)"
    
    def format_features_table(self, category: str) -> List[List[str]]:
        """Format features for display in a table"""
        features = self.features.get(category, {})
        rows = []
        
        for feature, info in features.items():
            status_emoji = {
                'completed': '✅',
                'partial': '🔶',
                'pending': '⬜'
            }.get(info['status'], '❓')
            
            rows.append([
                status_emoji,
                feature,
                info['description'],
                info.get('notes', '')
            ])
        
        return rows
    
    def update_feature(self, category: str, feature: str, status: str, notes: str) -> str:
        """Update a feature's status"""
        if category in self.features and feature in self.features[category]:
            # Update in memory
            self.features[category][feature]['status'] = status
            self.features[category][feature]['notes'] = notes
            
            # Save to persistent storage
            self.storage.update_feature_status(category, feature, status, notes)
            
            return f"✅ Updated {feature} to {status}"
        return f"❌ Feature not found: {category}/{feature}"
    
    def get_overall_stats(self) -> str:
        """Get overall completion statistics"""
        total = 0
        completed = 0
        partial = 0
        
        for category, features in self.features.items():
            for feature, info in features.items():
                total += 1
                if info['status'] == 'completed':
                    completed += 1
                elif info['status'] == 'partial':
                    partial += 1
        
        pending = total - completed - partial
        percentage = ((completed + partial * 0.5) / total * 100) if total > 0 else 0
        
        return f"""### 📊 Overall Progress

**Total Features:** {total}
**Completed:** {completed} ✅
**Partial:** {partial} 🔶
**Pending:** {pending} ⬜

**Overall Completion:** {percentage:.1f}%

---

### 📈 Implementation Velocity
- Core features are {completed/total*100:.0f}% complete
- {partial} features are in progress
- {pending} features await implementation
"""
    
    def get_priority_features(self) -> List[List[str]]:
        """Get high-priority pending features"""
        priority_features = []
        
        # Define priority categories
        priority_categories = [
            "Data Capture & Export",
            "Service & Characteristic Tools",
            "Security Testing",
            "Protocol Analysis"
        ]
        
        for category in priority_categories:
            if category in self.features:
                for feature, info in self.features[category].items():
                    if info['status'] == 'pending':
                        priority_features.append([
                            category,
                            feature,
                            info['description']
                        ])
                        if len(priority_features) >= 10:
                            return priority_features
        
        return priority_features
    
    def export_progress_report(self) -> str:
        """Export progress report"""
        report_file = self.storage.export_progress_report()
        return f"✅ Progress report exported to: {report_file}"
    
    def search_features(self, query: str) -> List[List[str]]:
        """Search features by name or description"""
        query = query.lower()
        results = []
        
        for category, features in self.features.items():
            for feature, info in features.items():
                if (query in feature.lower() or 
                    query in info['description'].lower() or
                    query in info.get('notes', '').lower()):
                    
                    status_emoji = {
                        'completed': '✅',
                        'partial': '🔶',
                        'pending': '⬜'
                    }.get(info['status'], '❓')
                    
                    results.append([
                        status_emoji,
                        category,
                        feature,
                        info['description']
                    ])
        
        return results if results else [["", "No results found", "", ""]]
    
    def generate_feature_context(self, category: str, feature: str) -> str:
        """Generate context for a single feature for Claude Code"""
        if category not in self.features or feature not in self.features[category]:
            return ""
        
        info = self.features[category][feature]
        context = f"""Feature: {feature}
Category: {category}
Status: {info['status']}
Description: {info['description']}"""
        
        if info.get('notes'):
            context += f"\nNotes: {info['notes']}"
        
        # Find related features in same category
        related = []
        for f, i in self.features[category].items():
            if f != feature and i['status'] != 'completed':
                related.append(f"- {f}: {i['description']}")
        
        if related:
            context += "\n\nRelated features in category:\n" + "\n".join(related[:5])
        
        return context
    
    def generate_implementation_prompt(self, features: List[Tuple[str, str]]) -> str:
        """Generate implementation context for multiple features"""
        if not features:
            return "No features selected"
        
        prompt = "I need to implement the following BlueFusion features:\n\n"
        
        for category, feature in features:
            if category in self.features and feature in self.features[category]:
                info = self.features[category][feature]
                prompt += f"**{feature}** ({category})\n"
                prompt += f"- Description: {info['description']}\n"
                prompt += f"- Current Status: {info['status']}\n"
                if info.get('notes'):
                    prompt += f"- Notes: {info['notes']}\n"
                prompt += "\n"
        
        prompt += "\nProject context:\n"
        prompt += "- BlueFusion is a BLE monitoring tool with dual interface support (native + USB sniffer)\n"
        prompt += "- Built with Swift backend and Python/Gradio frontend\n"
        prompt += "- WebSocket communication between backend and frontend\n"
        
        return prompt
    
    def get_pending_features_by_category(self, category: str) -> List[str]:
        """Get all pending features in a category"""
        features = self.features.get(category, {})
        return [f for f, info in features.items() if info['status'] == 'pending']
    
    def generate_category_context(self, category: str) -> str:
        """Generate context for an entire category"""
        if category not in self.features:
            return f"Category not found: {category}"
        
        features = self.features[category]
        completed = sum(1 for f in features.values() if f['status'] == 'completed')
        partial = sum(1 for f in features.values() if f['status'] == 'partial')
        pending = sum(1 for f in features.values() if f['status'] == 'pending')
        
        context = f"""Category: {category}
Progress: {completed} completed, {partial} partial, {pending} pending

Completed features:
"""
        for feature, info in features.items():
            if info['status'] == 'completed':
                context += f"✅ {feature}\n"
        
        context += "\nPending features:\n"
        for feature, info in features.items():
            if info['status'] == 'pending':
                context += f"⬜ {feature}: {info['description']}\n"
        
        if partial > 0:
            context += "\nPartially implemented:\n"
            for feature, info in features.items():
                if info['status'] == 'partial':
                    context += f"🔶 {feature}: {info['description']}\n"
                    if info.get('notes'):
                        context += f"   Notes: {info['notes']}\n"
        
        return context
    
    def generate_related_features(self, category: str, feature: str, max_features: int = 5) -> str:
        """Find and format related features that might need to be implemented together"""
        if category not in self.features:
            return ""
        
        # Keywords to identify related features
        feature_keywords = feature.lower().split()
        info = self.features[category].get(feature, {})
        desc_keywords = info.get('description', '').lower().split()
        all_keywords = set(feature_keywords + desc_keywords)
        
        # Find related features across all categories
        related = []
        
        for cat, features in self.features.items():
            for feat, feat_info in features.items():
                if feat == feature and cat == category:
                    continue
                
                # Check for keyword matches
                feat_text = f"{feat} {feat_info['description']}".lower()
                matches = sum(1 for kw in all_keywords if kw in feat_text and len(kw) > 3)
                
                if matches >= 2:  # At least 2 keyword matches
                    related.append({
                        'category': cat,
                        'feature': feat,
                        'info': feat_info,
                        'score': matches
                    })
        
        # Sort by relevance and status
        related.sort(key=lambda x: (x['info']['status'] != 'pending', -x['score']))
        
        if not related:
            return ""
        
        context = "\n\nRelated features to consider:\n"
        for item in related[:max_features]:
            status_emoji = {
                'completed': '✅',
                'partial': '🔶',
                'pending': '⬜'
            }.get(item['info']['status'], '❓')
            
            context += f"{status_emoji} {item['feature']} ({item['category']}): {item['info']['description']}\n"
        
        return context
    
    def format_features_table_with_selection(self, category: str) -> List[List]:
        """Format features table with selection checkboxes"""
        features = self.features.get(category, {})
        rows = []
        
        for feature, info in features.items():
            status_emoji = {
                'completed': '✅',
                'partial': '🔶',
                'pending': '⬜'
            }.get(info['status'], '❓')
            
            feature_id = f"{category}::{feature}"
            selected = feature_id in self.selected_features
            
            rows.append([
                selected,  # Checkbox column
                status_emoji,
                feature,
                info['description'],
                info.get('notes', '')
            ])
        
        return rows
    
    def toggle_feature_selection(self, category: str, feature: str) -> None:
        """Toggle selection of a feature"""
        feature_id = f"{category}::{feature}"
        if feature_id in self.selected_features:
            self.selected_features.remove(feature_id)
        else:
            self.selected_features.add(feature_id)
    
    def get_selected_features_context(self) -> str:
        """Generate context for all selected features"""
        if not self.selected_features:
            return "No features selected. Select features by clicking checkboxes in the feature table."
        
        features = []
        for feature_id in self.selected_features:
            category, feature = feature_id.split("::")
            features.append((category, feature))
        
        return self.generate_implementation_prompt(features)
    
    def clear_selection(self) -> None:
        """Clear all selected features"""
        self.selected_features.clear()
    
    def generate_quick_copy_formats(self, category: str, feature: str) -> Dict[str, str]:
        """Generate various copy formats for a feature"""
        if category not in self.features or feature not in self.features[category]:
            return {}
        
        info = self.features[category][feature]
        
        formats = {
            "feature_only": feature,
            "with_description": f"{feature}: {info['description']}",
            "markdown_task": f"- [ ] {feature}: {info['description']}",
            "full_context": self.generate_feature_context(category, feature),
            "implementation_request": f"Please implement the '{feature}' feature for BlueFusion. {info['description']}",
            "search_terms": f"{feature} {category} BLE Bluetooth {' '.join(info['description'].split()[:5])}"
        }
        
        # Add related features context
        related = self.generate_related_features(category, feature)
        if related:
            formats["with_related"] = formats["full_context"] + related
        
        return formats