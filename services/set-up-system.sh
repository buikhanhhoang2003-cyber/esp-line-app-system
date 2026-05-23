#!/bin/bash

# set-up-system.sh
# Complete setup script for LINE Messaging API System

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LINE Messaging API System Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Ask for tokens directly
echo ""
echo -e "${BLUE}Enter your LINE Channel Access Token:${NC}"
read -p "> " LINE_CHANNEL_ACCESS_TOKEN

echo -e "${BLUE}Enter your LINE Group ID (starts with C, optional):${NC}"
read -p "> " LINE_GROUP_ID

# Create .env file
echo -e "${GREEN}Creating .env file...${NC}"
cat > .env << EOF
# LINE API Configuration
LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
LINE_GROUP_ID=${LINE_GROUP_ID}

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=info
API_PORT=8000

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
EOF

echo -e "${GREEN}✓ .env file created${NC}"

# Load environment variables
source .env

# Check Python version
echo -e "${GREEN}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Python $required_version or higher is required${NC}"
    exit 1
fi
echo -e "${GREEN}Python $python_version detected${NC}"

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies from requirements.txt...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p docker/logs
mkdir -p data
mkdir -p backups

# Set permissions
echo -e "${GREEN}Setting permissions...${NC}"
chmod +x docker/*.sh 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

# Test configuration
echo -e "${GREEN}Testing configuration...${NC}"
python3 -c "
from config.config import config
print('✓ Config loaded successfully')
print(f'✓ Token configured: {bool(config.line_access_token)}')
print(f'✓ Group ID configured: {bool(config.group_id)}')
"

# Run tests
echo -e "${GREEN}Running tests...${NC}"
if [ -d "test" ]; then
    python3 -m pytest test/ -v || echo -e "${YELLOW}Some tests failed, but continuing...${NC}"
fi

# Docker setup (optional)
read -p "Do you want to build and run with Docker? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Setting up Docker containers...${NC}"
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    # Build and run with docker-compose
    cd docker
    docker-compose build
    docker-compose up -d
    cd ..
    
    echo -e "${GREEN}Docker containers started${NC}"
    echo -e "${GREEN}API is running at http://localhost:8000${NC}"
else
    # Run locally
    echo -e "${GREEN}Starting API server locally...${NC}"
    echo -e "${GREEN}API will be available at http://localhost:8000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    
    # Run with uvicorn
    uvicorn esp-line-app-system.services.api.line_app.endpoints:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info
fi

# Create systemd service (optional for production)
if [ "$ENVIRONMENT" = "production" ]; then
    read -p "Create systemd service for auto-start? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo cat > /etc/systemd/system/line-api.service << EOF
[Unit]
Description=LINE Messaging API Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin"
ExecStart=$PWD/venv/bin/uvicorn esp-line-app-system.services.api.line_app.endpoints:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable line-api
        sudo systemctl start line-api
        echo -e "${GREEN}Systemd service created and started${NC}"
    fi
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "API Documentation: http://localhost:8000/docs"
echo -e "Health Check: http://localhost:8000/health"
echo -e "Config Info: http://localhost:8000/config"