#!/bin/bash

# SIA-Broker Startup Script
# This script starts the FastAPI SIA-DC alarm notification broker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  SIA-DC Alarm Broker Startup"
echo "=============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo "Please review and update .env with your settings"
    else
        echo -e "${RED}✗ .env.example not found!${NC}"
        echo "Please create a .env file manually"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found${NC}"
    echo "Would you like to create one? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed${NC}"
    echo "Installing dependencies from app/requirements.txt..."
    pip install -r app/requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Display configuration
echo ""
echo "Configuration:"
echo "  SIA Host: ${SIA_HOST:-0.0.0.0}"
echo "  SIA Port: ${SIA_PORT:-65100}"
echo "  Accounts: ${SIA_ACCOUNTS:-AAA}"
echo "  Forward URL: ${FORWARD_URL:-http://localhost:9000/ingest}"
echo "  Timezone: ${APP_TIMEZONE:-Asia/Jakarta}"
echo "  Log Level: ${LOG_LEVEL:-INFO}"
echo ""

# Check if port is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}✗ Port 8000 is already in use${NC}"
    echo "Please stop the existing process or use a different port"
    echo "To find the process: lsof -i :8000"
    exit 1
fi

# Start the application
echo "=============================================="
echo "Starting SIA-DC Broker on http://0.0.0.0:8000"
echo "SIA-DC TCP listener on port ${SIA_PORT:-65100}"
echo "=============================================="
echo "Press Ctrl+C to stop"
echo ""

# Run uvicorn with options
# Adjust host, port, and workers as needed
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level "${LOG_LEVEL:-info}" \
    --no-access-log
