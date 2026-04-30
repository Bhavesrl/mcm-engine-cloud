@echo off
echo ============================================
echo  MCM Engine - Avvio entrambi i server
echo ============================================
echo.
echo  Flask (UI completa):  http://localhost:5001
echo  React (explorer):     http://localhost:5173
echo.
echo Premere CTRL+C in ciascuna finestra per fermare.
echo.

start "MCM - Flask" cmd /k "python run.py"
timeout /t 2 /nobreak >nul
start "MCM - React" cmd /k "cd frontend && npm run dev"
