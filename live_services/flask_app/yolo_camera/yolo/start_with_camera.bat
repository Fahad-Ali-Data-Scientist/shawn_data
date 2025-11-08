@echo off
echo ================================================================
echo YOLO Detection System - HTTP Camera Enabled
echo ================================================================
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set IP=%%a
set IP=%IP:~1%

echo Your Server IP: %IP%
echo.
echo Starting Flask server...
echo.

REM Start Flask server in background
start /B python app.py

REM Wait for server to start
timeout /t 3 /nobreak >nul

echo.
echo ================================================================
echo Server is running!
echo ================================================================
echo.
echo Access from this computer: http://localhost:5000
echo Access from other devices: http://%IP%:5000
echo.
echo ================================================================
echo Opening Chrome with camera enabled...
echo ================================================================
echo.

REM Launch Chrome with insecure origin flag
start chrome --unsafely-treat-insecure-origin-as-secure="http://%IP%:5000" --user-data-dir="%TEMP%\chrome_camera" "http://%IP%:5000"

echo.
echo Chrome opened with camera enabled!
echo.
echo Press Ctrl+C to stop the server
echo.
pause

