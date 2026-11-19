@echo off
title 4-Agent Gaming Shorts Studio (k1, k2, k3, k4)
echo ===================================================
echo     🎮 4-AGENT GAMING SHORTS & REELS STUDIO
echo ===================================================
echo   k1: YouTube Gaming Video Researcher (GTA 5/6)
echo   k2: Shorts & Meme Content Creator (Karaoke & Memes)
echo   k3: YouTube Shorts Publisher (With Creator Credits)
echo   k4: Instagram Reels Publisher (With Creator Credits)
echo ===================================================

cd /d "%~dp0"
call .venv\Scripts\activate.bat

python scripts\orchestrate_k_agents.py --status

echo.
echo Options:
echo   1. Check Pipeline Status
echo   2. Run k1 (Search GTA 6 Videos)
echo   3. Run k2 (Create Meme Shorts from Queue)
echo   4. Run k3 (Publish Next YouTube Short with Credits)
echo   5. Run k4 (Publish Next Instagram Reel with Credits)
echo   6. Configure / Login Instagram Account for k4
echo   7. Run All 4 Agents End-to-End
echo   8. Exit
echo.

set /p opt="Select an option (1-8): "

if "%opt%"=="1" python scripts\orchestrate_k_agents.py --status
if "%opt%"=="2" python scripts\k1_researcher.py --query "GTA 6 gameplay" --max-results 3
if "%opt%"=="3" python scripts\k2_shorts_creator.py --auto-queue
if "%opt%"=="4" python scripts\k3_youtube_publisher.py --publish-next
if "%opt%"=="5" python scripts\k4_instagram_publisher.py --publish-next
if "%opt%"=="6" python scripts\setup_instagram.py
if "%opt%"=="7" python scripts\orchestrate_k_agents.py --all
if "%opt%"=="8" exit /b 0

pause
