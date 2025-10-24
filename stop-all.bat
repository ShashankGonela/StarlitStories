@echo off
echo ========================================
echo Stopping Starlit Stories
echo ========================================
echo.

echo Killing backend processes (Python/Uvicorn)...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.12.exe 2>nul

echo Killing frontend processes (Node/Vite)...
taskkill /F /IM node.exe 2>nul

echo.
echo Killing by port...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /F /PID %%a 2>nul

echo.
echo ========================================
echo All servers stopped!
echo ========================================
timeout /t 3
