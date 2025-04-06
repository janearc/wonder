#!/bin/bash

# Exit on error
set -e

# Deactivate any active virtual environment
deactivate 2>/dev/null || true

# Remove existing virtual environment if it exists
rm -rf .venv

# Create new virtual environment with Python 3.12
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install poetry typer rich pyyaml

# Install the Wonder tool in development mode
cd tools/wonder
pip install -e .
cd ../..

# Install the Gizzard tool in development mode
cd tools/gizzard
pip install -e .
cd ../..

# Install the Wonder Local tool in development mode
cd tools/wonder-local
pip install -e .
cd ../..

# Create wrapper script for wonder command
VENV_BIN_DIR=$(dirname $(which python))
cat > "$VENV_BIN_DIR/wonder" << 'EOF'
#!/bin/bash
python -m wonder.cli "$@"
EOF
chmod +x "$VENV_BIN_DIR/wonder"

echo "✨ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To verify installation:"
echo "  wonder list-picokernels" 