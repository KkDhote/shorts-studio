@echo off
title Shorts Studio & Profit Maximizer
echo ===================================================
echo     SHORTS STUDIO & PROFIT MAXIMIZER DASHBOARD
echo ===================================================
echo Starting local web server on port 5050...

cd /d "%~dp0"
call .venv\Scripts\activate.bat

start http://localhost:5050
start /B bin\cloudflared.exe tunnel --url http://localhost:5050
python web\app.py
pause
