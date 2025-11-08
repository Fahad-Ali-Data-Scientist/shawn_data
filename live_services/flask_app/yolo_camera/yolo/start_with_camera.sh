#!/bin/bash

echo "================================================================"
echo "YOLO Detection System - HTTP Camera Enabled"
echo "================================================================"
echo ""

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
else
    # Linux
    IP=$(hostname -I | awk '{print $1}')
fi

echo "Your Server IP: $IP"
echo ""
echo "Starting Flask server..."
echo ""

# Start Flask server in background
python app.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo ""
echo "================================================================"
echo "Server is running!"
echo "================================================================"
echo ""
echo "Access from this computer: http://localhost:5000"
echo "Access from other devices: http://$IP:5000"
echo ""
echo "================================================================"
echo "Opening Chrome with camera enabled..."
echo "================================================================"
echo ""

# Launch Chrome with insecure origin flag
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open -na "Google Chrome" --args --unsafely-treat-insecure-origin-as-secure="http://$IP:5000" --user-data-dir="/tmp/chrome_camera" "http://$IP:5000"
else
    # Linux
    google-chrome --unsafely-treat-insecure-origin-as-secure="http://$IP:5000" --user-data-dir="/tmp/chrome_camera" "http://$IP:5000" &
fi

echo ""
echo "Chrome opened with camera enabled!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for Ctrl+C
trap "kill $SERVER_PID; exit" INT
wait $SERVER_PID

