@echo off
title AI Wi-Fi Dead-Zone Prediction & AP Optimization Launcher
echo ============================================================
echo AI-Based Wi-Fi Coverage Optimization & Dead-Zone Prediction
echo Major Project System Launcher
echo ============================================================
echo.
echo Launching Backend and Frontend concurrently...
echo.

start "Backend Server (FastAPI)" cmd /c "%~dp0start_backend.bat"
timeout /t 3 /nobreak >nul
start "Frontend Dashboard (Vite)" cmd /c "%~dp0start_frontend.bat"

echo System started!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://localhost:8000/docs
echo.
pause
