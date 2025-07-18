#!/bin/bash

# BlueFusion Release Preparation Script
# This script creates a consumer-ready distribution package

set -e

VERSION=${1:-"1.0.0"}
RELEASE_DIR="public/releases/bluefusion-v${VERSION}"
DIST_NAME="bluefusion-v${VERSION}"

echo "Preparing BlueFusion release v${VERSION}..."

# Create release directory structure
mkdir -p public/releases
rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"

# Copy source files
echo "Copying source files..."
cp -r src "${RELEASE_DIR}/"
# Copy public directory but exclude releases subdirectory
mkdir -p "${RELEASE_DIR}/public"
for item in public/*; do
    if [ "$(basename "$item")" != "releases" ]; then
        cp -r "$item" "${RELEASE_DIR}/public/"
    fi
done

# Copy documentation
echo "Copying documentation..."
cp README.md "${RELEASE_DIR}/"
cp CONTRIBUTORS.md "${RELEASE_DIR}/"
cp LICENSE "${RELEASE_DIR}/" 2>/dev/null || echo "No LICENSE file found"

# Copy configuration files
echo "Copying configuration files..."
cp requirements.txt "${RELEASE_DIR}/"
cp install.sh "${RELEASE_DIR}/"
cp .gitignore "${RELEASE_DIR}/"

# Create example configuration if exists
if [ -f "config.example.json" ]; then
    cp config.example.json "${RELEASE_DIR}/"
fi

# Clean up unnecessary files
echo "Cleaning up..."
find "${RELEASE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${RELEASE_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${RELEASE_DIR}" -type f -name ".DS_Store" -delete 2>/dev/null || true

# Create version file
echo "${VERSION}" > "${RELEASE_DIR}/VERSION"

# Create quick start guide
cat > "${RELEASE_DIR}/QUICK_START.md" << EOF
# BlueFusion Quick Start Guide

## Installation

1. Run the installer:
   \`\`\`bash
   ./install.sh
   \`\`\`

2. Activate the virtual environment:
   - Unix/macOS: \`source venv/bin/activate\`
   - Windows: \`venv\\Scripts\\activate\`

3. Start BlueFusion:
   \`\`\`bash
   python -m src.api.fastapi_server
   \`\`\`

4. Open your browser to http://localhost:8000

For detailed instructions, see README.md
EOF

# Create ZIP archive
echo "Creating ZIP archive..."
cd public/releases
zip -r "${DIST_NAME}.zip" "bluefusion-v${VERSION}"

# Create TAR.GZ archive
echo "Creating TAR.GZ archive..."
tar -czf "${DIST_NAME}.tar.gz" "bluefusion-v${VERSION}"

cd ../..

echo ""
echo "Release preparation complete!"
echo "Archives created:"
echo "  - public/releases/${DIST_NAME}.zip"
echo "  - public/releases/${DIST_NAME}.tar.gz"
echo ""
echo "To publish this release:"
echo "1. Create a new release on GitHub"
echo "2. Upload the archives as release assets"
echo "3. Tag the release as v${VERSION}"