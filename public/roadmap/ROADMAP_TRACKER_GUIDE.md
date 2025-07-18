# BlueFusion Roadmap Tracker Guide

## Overview
The Roadmap TODO tracker in BlueFusion helps you track feature implementation progress and generate context for Claude Code. This guide shows you how to use the new context generation features effectively.

## Features

### 1. **Quick Copy Actions** ⚡
Select any feature and instantly copy formatted text:
- **📝 Feature Name**: Just the feature name
- **📄 Name + Description**: Feature with its description
- **☑️ Markdown Task**: GitHub-style task checkbox format
- **💬 Implementation Request**: Ready-to-paste Claude Code prompt

### 2. **Context Generation** 📋
Generate comprehensive context for Claude Code:
- **Feature Context**: Detailed info about a single feature with related features
- **Category Overview**: Complete status of all features in a category
- **Implementation Prompt**: Full implementation request with project context
- **Selected Features**: Context for multiple selected features (batch operations)

### 3. **Search & Filter** 🔍
- Search across all 150+ features by name or description
- Filter by category
- View high-priority pending features

### 4. **Progress Tracking** 📊
- Real-time completion statistics
- Category-wise progress
- Export progress reports
- Persistent storage of feature status

## Usage Examples

### Example 1: Implementing a Single Feature
1. Navigate to "Roadmap TODO" tab
2. Select category (e.g., "Data Capture & Export")
3. Choose a feature (e.g., "CSV Export")
4. Click "💬 Implementation Request" for quick copy
5. Paste into Claude Code

**Generated prompt:**
```
Please implement the 'CSV Export' feature for BlueFusion. Export captured data to CSV format
```

### Example 2: Getting Full Context
1. Select a feature
2. Choose "Feature Context" in Context Type
3. Click "Generate Context"
4. Copy the generated text

**Generated context includes:**
- Feature details
- Current status
- Implementation notes
- Related features in the category
- Similar features across categories

### Example 3: Planning Multiple Features
1. Select "Category Overview" in Context Type
2. Click "Generate Context"
3. Get complete status of all features in that category
4. See what's completed, partial, and pending

### Example 4: Implementation Workflow
1. Search for a feature (e.g., "export")
2. Review search results showing all export-related features
3. Select the specific feature you want
4. Generate implementation context
5. Update status to "partial" when you start
6. Add notes about progress
7. Mark as "completed" when done

## Tips for Claude Code Integration

### Providing Context
When starting a new feature implementation:
```
1. Copy the feature's implementation prompt
2. Add any relevant code paths
3. Include current architecture notes
4. Paste into Claude Code
```

### Tracking Progress
- Update feature status in real-time
- Add implementation notes for future reference
- Export progress reports for documentation

### Finding Related Features
The tracker automatically finds related features based on:
- Keyword matching
- Category relationships
- Technical dependencies

## Keyboard Shortcuts (Future Enhancement)
- `Ctrl+C`: Copy selected feature context
- `Ctrl+F`: Focus search box
- `Tab`: Navigate between features

## Best Practices

1. **Before Implementation**
   - Check feature status (might be partially done)
   - Review related features
   - Generate full context

2. **During Implementation**
   - Update status to "partial"
   - Add notes about approach
   - Link to relevant code files

3. **After Implementation**
   - Mark as completed
   - Document any limitations
   - Update related features if needed

## Advanced Usage

### Batch Operations
1. Search for related features (e.g., all "security" features)
2. Review the list
3. Generate implementation context for the group
4. Plan implementation order

### Export Formats
- **Progress Report**: JSON file with all feature statuses
- **Category Context**: Markdown-formatted overview
- **Implementation Plan**: Ready-to-use development plan

## Storage Location
Feature status is saved to: `~/.bluefusion/roadmap_status.json`

This ensures your progress persists between sessions and can be shared with team members.