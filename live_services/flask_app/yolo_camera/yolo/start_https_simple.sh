#!/bin/bash

echo "================================================================"
echo "YOLO Detection - HTTPS Setup (No Signup Required!)"
echo "================================================================"
echo ""
echo "This uses Cloudflare Tunnel - No account needed!"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    echo ""
    
    # Detect architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -O cloudflared
    else
        echo "Unsupported architecture: $ARCH"
        exit 1
    fi
    
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    
    echo "✅ cloudflared installed!"
    echo ""
fi

echo "================================================================"
echo "Starting Flask server..."
echo "================================================================"
echo ""

# Start Flask in background
python3 app.py > flask.log 2>&1 &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

echo "✅ Flask server started"
echo ""
echo "================================================================"
echo "Starting HTTPS tunnel..."
echo "================================================================"
echo ""
echo "⏳ Getting your HTTPS URL... (takes 5-10 seconds)"
echo ""

# Start cloudflared and capture output
cloudflared tunnel --url http://localhost:5000 > tunnel.log 2>&1 &
TUNNEL_PID=$!

# Wait for URL to be ready
sleep 8

# Extract URL from log
HTTPS_URL=$(grep -o 'https://.*trycloudflare.com' tunnel.log | head -n 1)

if [ -z "$HTTPS_URL" ]; then
    echo "⚠️  Could not auto-detect URL"
    echo "Checking tunnel log..."
    cat tunnel.log | grep https://
else
    echo ""
    echo "================================================================"
    echo "✅ YOUR HTTPS URL IS READY!"
    echo "================================================================"
    echo ""
    echo "   🌐 $HTTPS_URL"
    echo ""
    echo "================================================================"
    echo ""
    echo "📱 SHARE THIS URL WITH YOUR CLIENTS!"
    echo ""
    echo "They can:"
    echo "  1. Open the URL above"
    echo "  2. Click 'Live Camera Detection'"
    echo "  3. Allow camera permissions"
    echo "  4. Start using immediately!"
    echo ""
    echo "✅ NO browser setup needed for clients!"
    echo "✅ Works on mobile and desktop!"
    echo "✅ Camera works automatically!"
    echo ""
    echo "================================================================"
    echo ""
    echo "Server is running. Press Ctrl+C to stop."
    echo ""
    echo "================================================================"
fi

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $TUNNEL_PID 2>/dev/null
    rm -f flask.log tunnel.log
    echo "Stopped."
    exit 0
}

trap cleanup INT TERM

# Keep script running
wait

