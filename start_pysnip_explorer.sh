#!/bin/bash
# start_pysnip_explorer.sh
# Script to start the PySnip Explorer web interface

# Set the path to your PySnip directory
export PYSNIP_ROOT = /sdcard/1dd1/projects/personal/current/pysnip

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}PySnip Explorer Startup Script${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found.${NC}"
    echo -e "Please run this script from the PySnip Explorer directory."
    exit 1
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Warning: Virtual environment not found.${NC}"
    echo -e "Running without virtual environment."
fi

# Check if Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${RED}Error: Flask is not installed.${NC}"
    echo -e "Please install requirements using: pip install -r requirements.txt"
    exit 1
fi

# Check if PySnip directory exists
if [ ! -d "$PYSNIP_ROOT" ]; then
    echo -e "${YELLOW}Warning: PySnip directory not found at $PYSNIP_ROOT${NC}"
    echo -e "Please update the PYSNIP_ROOT variable in this script."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get network information
IP_ADDRESS=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

# Start the Flask app
echo -e "${GREEN}Starting PySnip Explorer...${NC}"
echo -e "${BLUE}Local URL:${NC} http://localhost:5000"
echo -e "${BLUE}Network URL:${NC} http://$IP_ADDRESS:5000"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo

# Start Flask
python app.py

# This point is only reached if the Flask app stops
echo
echo -e "${RED}PySnip Explorer has stopped.${NC}"
