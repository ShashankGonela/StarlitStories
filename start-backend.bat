@echo off
REM Starlit Stories - Backend Startup Script
REM Starts the FastAPI server

echo ========================================
echo    Starlit Stories - Backend Server
echo ========================================
echo.

echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python -m src.api.server

pause
