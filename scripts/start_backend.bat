@echo off
title Wi-Fi Dead-Zone Prediction - Backend Server
echo Starting FastAPI Backend Server on http://localhost:8000...
cd /d "%~dp0\.."
set PYTHONPATH=backend
.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
