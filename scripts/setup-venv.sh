#!/bin/bash

# Exit on error
set -e

# Ensure we're in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🔧 Setting up virtual environment..."

# Create new venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install core dependencies
echo "📦 Installing core dependencies..."
pip install --upgrade pip
pip install invoke==2.2.0 pyyaml==6.0.1 rich==13.7.0

# Verify invoke is installed
if ! python -c "import invoke" 2>/dev/null; then
    echo "❌ Failed to install invoke"
    exit 1
fi

# Verify other dependencies
if ! python -c "import yaml, rich" 2>/dev/null; then
    echo "❌ Failed to install required dependencies"
    exit 1
fi

# Create wonder wrapper script
cat > .venv/bin/wonder << EOF
#!/bin/bash
SCRIPT_DIR="\$(dirname "\$0")"
source "\$SCRIPT_DIR/activate"
python -m invoke "\$@"
EOF
chmod +x .venv/bin/wonder

echo "✨ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To verify installation:"
echo "  wonder list-picokernels" 