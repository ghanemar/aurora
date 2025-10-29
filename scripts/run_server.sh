#!/bin/bash
# Start Aurora FastAPI server on port 8001

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file. Please review and update with your settings."
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Run 'poetry shell' to activate the environment first."
    exit 1
fi

# Start server
echo "🚀 Starting Aurora server on http://localhost:8001"
echo "📚 API documentation: http://localhost:8001/docs"
echo "🔄 Press Ctrl+C to stop"
echo ""

uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
