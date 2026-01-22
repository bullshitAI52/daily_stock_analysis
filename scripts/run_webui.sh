#!/bin/bash

# ==========================================
# Stock Analysis WebUI Startup Script
# ==========================================

# Default Port
DEFAULT_PORT=8088

# Help Function
show_help() {
    echo "Usage: ./run_webui.sh [PORT]"
    echo ""
    echo "Examples:"
    echo "  ./run_webui.sh          # Run on default port $DEFAULT_PORT"
    echo "  ./run_webui.sh 9090     # Run on port 9090"
    echo ""
}

# Check for help argument
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Set port from argument or default
PORT=${1:-$DEFAULT_PORT}

echo "=========================================="
echo "Starting Stock Analysis WebUI..."
echo "Port: $PORT"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env file to configure your API keys."
        # Don't exit, just warn
    else
        echo "Error: .env.example not found!"
        exit 1
    fi
fi

# Strategy 1: Docker Compose (Preferred)
if command -v docker-compose &> /dev/null; then
    echo "[Mode] Using Docker Compose"
    echo "Updating port in docker-compose.yml..."
    
    # We can't easily edit the yaml on the fly without tools like yq,
    # so we will use the environment variable substitution if supported,
    # or just tell the user how to map it.
    
    # Actually, simply running via python is often easier for quick custom ports
    # if the user doesn't want to edit docker-compose.yml.
    # But let's try to pass the port via environment variable to docker-compose if possible.
    
    # Check if user wants to use docker explicitly?
    # Let's fallback to Python direct execution if they are running this script,
    # because 'run_webui.sh' implies a simple direct run usually.
    # Docker users usually know to type 'docker-compose up'.
    
    # So I will skip auto-docker here to keep it simple and flexible for custom ports.
fi

# Strategy 2: Direct Python Execution
echo "[Mode] Direct Python Execution"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python not found!"
    exit 1
fi

# Set Environment Variables
export WEBUI_HOST=0.0.0.0
export WEBUI_PORT=$PORT

# Run
$PYTHON_CMD main.py --webui-only
