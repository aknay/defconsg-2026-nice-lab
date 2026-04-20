#!/bin/bash

set -e  # exit on error

# Find a usable Python interpreter
for py in python3 python; do
    if command -v $py &> /dev/null; then
        PYTHON_BIN=$py
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python not found. Please install Python 3."
    exit 1
fi

echo "🐍 Using Python: $PYTHON_BIN"
$PYTHON_BIN --version

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_BIN -m venv .venv
else
    echo "✅ Virtual environment already exists."
fi

echo "⚡ Activating virtual environment..."
source .venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
fi

echo "🎉 Setup complete!"