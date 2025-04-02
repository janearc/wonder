#!/bin/bash

# Exit on error
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Create virtual environment if it doesn't exist
if [ ! -d "$SYSTEM_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SYSTEM_DIR/venv"
fi

# Activate virtual environment
source "$SYSTEM_DIR/venv/bin/activate"

# Install required packages
echo "Installing required packages..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Make gizzard executable
chmod +x "$SCRIPT_DIR/gizzard"

echo "Gizzard environment setup complete!"
echo "To use gizzard, first activate the virtual environment:"
echo "source $SYSTEM_DIR/venv/bin/activate" 