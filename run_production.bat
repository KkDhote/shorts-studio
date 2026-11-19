@echo off
title Shorts Studio - Production Server
cd /d "%~dp0"

echo ========================================================
echo   Starting Shorts Studio & Autonomous Publishing Engine
echo ========================================================

REM Run using Python in background
start /b "" .\.venv\Scripts\python.exe web\app.py
start /b "" .\bin\cloudflared.exe tunnel --url http://localhost:5050

echo [OK] Studio running at http://localhost:5050
echo [OK] Cloudflare tunnel active for mobile access.
