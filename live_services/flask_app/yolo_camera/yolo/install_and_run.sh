#!/bin/bash

echo "================================================================"
echo "🎯 YOLO Detection System - Auto Setup & Run"
echo "================================================================"
echo ""

# Step 1: Install cloudflared if needed
echo "Step 1/3: Checking cloudflared..."
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -O cloudflared
    fi
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    echo "✅ cloudflared installed"
else
    echo "✅ cloudflared already installed"
fi
echo ""

# Step 2: Check Python dependencies
echo "Step 2/3: Checking Python dependencies..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✅ Dependencies look good"
else
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi
echo ""

# Step 3: Start everything
echo "Step 3/3: Starting servers..."
echo ""
echo "================================================================"
echo "🚀 LAUNCHING..."
echo "================================================================"
echo ""

# Make script executable
chmod +x start_https_simple.sh

# Run the HTTPS script
./start_https_simple.sh

