#!/bin/bash

echo "================================================================"
echo "YOLO Detection System - HTTPS Setup with ngrok"
echo "================================================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo ""
    echo "Installing ngrok..."
    echo ""
    
    # Detect OS and install
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Downloading ngrok for Linux..."
        wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar xvzf ngrok-v3-stable-linux-amd64.tgz
        sudo mv ngrok /usr/local/bin/
        rm ngrok-v3-stable-linux-amd64.tgz
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "Installing ngrok via Homebrew..."
        brew install ngrok/ngrok/ngrok
    fi
    
    echo ""
    echo "✅ ngrok installed!"
    echo ""
fi

# Check if ngrok authtoken is set
echo "Checking ngrok authentication..."
if ! ngrok config check &> /dev/null; then
    echo ""
    echo "⚠️  ngrok needs authentication token"
    echo ""
    echo "1. Go to: https://dashboard.ngrok.com/signup"
    echo "2. Sign up (free)"
    echo "3. Copy your authtoken"
    echo "4. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    read -p "Press Enter after setting up ngrok authtoken..."
fi

echo ""
echo "================================================================"
echo "Starting Flask server..."
echo "================================================================"
echo ""

# Start Flask in background
python3 app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

echo ""
echo "================================================================"
echo "Starting ngrok tunnel (HTTPS)..."
echo "================================================================"
echo ""

# Start ngrok
ngrok http 5000 --log=stdout &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

echo ""
echo "================================================================"
echo "Getting your HTTPS URL..."
echo "================================================================"
echo ""

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -n 1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Could not get ngrok URL"
    echo "Please check: http://localhost:4040"
else
    echo "✅ Your HTTPS URL is ready!"
    echo ""
    echo "================================================================"
    echo "🌐 ACCESS YOUR APP:"
    echo "================================================================"
    echo ""
    echo "   $NGROK_URL"
    echo ""
    echo "================================================================"
    echo ""
    echo "✅ Clients can now:"
    echo "   1. Open the URL above"
    echo "   2. Click 'Live Camera Detection'"
    echo "   3. Use camera directly - NO SETUP NEEDED!"
    echo ""
    echo "📊 Monitor ngrok: http://localhost:4040"
    echo ""
    echo "================================================================"
    echo "Press Ctrl+C to stop both servers"
    echo "================================================================"
fi

# Cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Keep script running
wait

