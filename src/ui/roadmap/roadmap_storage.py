"""
Persistent storage for roadmap feature status
"""
import json
import os
from pathlib import Path
from datetime import datetime

class RoadmapStorage:
    def __init__(self):
        # Store in user's home directory under .bluefusion
        self.storage_dir = Path.home() / ".bluefusion"
        self.storage_file = self.storage_dir / "roadmap_status.json"
        self.ensure_storage_exists()
        
    def ensure_storage_exists(self):
        """Create storage directory if it doesn't exist"""
        self.storage_dir.mkdir(exist_ok=True)
        
    def load_status(self):
        """Load feature status from persistent storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading roadmap status: {e}")
                return {}
        return {}
    
    def save_status(self, status_data):
        """Save feature status to persistent storage"""
        try:
            # Add metadata
            status_data['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving roadmap status: {e}")
            return False
    
    def update_feature_status(self, category, feature, status, notes=""):
        """Update a single feature's status"""
        data = self.load_status()
        
        if category not in data:
            data[category] = {}
        
        data[category][feature] = {
            'status': status,
            'notes': notes,
            'updated_at': datetime.now().isoformat()
        }
        
        return self.save_status(data)
    
    def get_feature_status(self, category, feature):
        """Get status for a specific feature"""
        data = self.load_status()
        if category in data and feature in data[category]:
            return data[category][feature].get('status', 'pending')
        return 'pending'
    
    def merge_with_defaults(self, default_features):
        """Merge saved status with default feature list"""
        saved_data = self.load_status()
        
        # Update default features with saved status
        for category, features in default_features.items():
            if category in saved_data:
                for feature, info in features.items():
                    if feature in saved_data[category]:
                        # Update status from saved data
                        info['status'] = saved_data[category][feature].get('status', info['status'])
                        # Add notes if available
                        if 'notes' in saved_data[category][feature]:
                            info['notes'] = saved_data[category][feature]['notes']
        
        return default_features
    
    def export_progress_report(self):
        """Generate a progress report"""
        from .roadmap_tracker import ROADMAP_FEATURES, get_feature_stats
        
        # Merge saved status with defaults
        features = self.merge_with_defaults(ROADMAP_FEATURES.copy())
        stats = get_feature_stats()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'features': features
        }
        
        # Save report
        report_file = self.storage_dir / f"progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file