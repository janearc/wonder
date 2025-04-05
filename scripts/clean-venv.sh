#!/bin/bash

# Ensure we're in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🧹 Cleaning virtual environment..."

# Deactivate if in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Remove existing venv
rm -rf .venv

echo "✨ Virtual environment cleaned!"
echo "Run './scripts/setup-venv.sh' to create a new environment" 