@echo off
echo ================================================================
echo YOLO Detection System - HTTPS Setup with ngrok
echo ================================================================
echo.

REM Check if ngrok exists
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ngrok is not installed!
    echo.
    echo Installing ngrok...
    echo.
    echo Please download ngrok from: https://ngrok.com/download
    echo After downloading:
    echo 1. Extract ngrok.exe
    echo 2. Move it to C:\Windows\System32\
    echo 3. Run this script again
    echo.
    pause
    exit /b
)

echo Checking ngrok authentication...
ngrok config check >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ngrok needs authentication token
    echo.
    echo 1. Go to: https://dashboard.ngrok.com/signup
    echo 2. Sign up free
    echo 3. Copy your authtoken
    echo 4. Run: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
)

echo.
echo ================================================================
echo Starting Flask server...
echo ================================================================
echo.

REM Start Flask in background
start /B python app.py

REM Wait for Flask to start
timeout /t 5 /nobreak >nul

echo.
echo ================================================================
echo Starting ngrok tunnel HTTPS...
echo ================================================================
echo.

REM Start ngrok in new window
start "ngrok" ngrok http 5000

REM Wait for ngrok to start
timeout /t 5 /nobreak >nul

echo.
echo ================================================================
echo Getting your HTTPS URL...
echo ================================================================
echo.

REM Try to get ngrok URL using PowerShell
for /f "delims=" %%i in ('powershell -Command "(Invoke-WebRequest -Uri 'http://localhost:4040/api/tunnels').Content | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Where-Object {$_.proto -eq 'https'} | Select-Object -ExpandProperty public_url"') do set NGROK_URL=%%i

if "%NGROK_URL%"=="" (
    echo Could not auto-detect ngrok URL
    echo Please check: http://localhost:4040
) else (
    echo Your HTTPS URL is ready!
    echo.
    echo ================================================================
    echo ACCESS YOUR APP:
    echo ================================================================
    echo.
    echo    %NGROK_URL%
    echo.
    echo ================================================================
    echo.
    echo Clients can now:
    echo    1. Open the URL above
    echo    2. Click 'Live Camera Detection'
    echo    3. Use camera directly - NO SETUP NEEDED!
    echo.
    echo Monitor ngrok: http://localhost:4040
    echo.
    echo ================================================================
)

echo.
echo Press Ctrl+C to stop both servers
echo.
pause

