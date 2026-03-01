#!/bin/bash
# Build script for Linux/Ubuntu
# Usage: ./build.sh

echo "TV Viewer - Linux Build Script"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is required"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist TV_Viewer.spec __pycache__

# Build executable
echo "Building executable..."
python3 build.py --onefile

if [ -f "dist/TV_Viewer" ]; then
    chmod +x dist/TV_Viewer
    echo ""
    echo "================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================"
    echo "Executable: $(pwd)/dist/TV_Viewer"
    echo ""
    echo "To run: ./dist/TV_Viewer"
    echo ""
    echo "NOTE: VLC must be installed:"
    echo "  sudo apt install vlc libvlc-dev"
else
    echo "Build failed!"
    exit 1
fi
