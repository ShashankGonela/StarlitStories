@echo off
REM Starlit Stories - Start Both Backend and Frontend

echo ========================================
echo    Starlit Stories - Full Stack
echo ========================================
echo.
echo Starting backend and frontend servers...
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.
echo Press Ctrl+C in each window to stop the servers
echo.
pause

echo Opening backend server...
start "Starlit Stories - Backend" cmd /k "python -m src.api.server"

timeout /t 3 /nobreak > nul

echo Opening frontend server...
start "Starlit Stories - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting...
echo Check the new console windows for status
echo.
pause
