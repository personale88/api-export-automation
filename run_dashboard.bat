@echo off
title Singing Bowls Export Automation Hub
cd /d "%~dp0"
echo =================================================================
echo       EXPORT AUTOMATION SYSTEM (API 3) - WEB DASHBOARD
echo       Starting Flask Local Server on http://127.0.0.1:5000
echo       NOTE: Keep this window open while using the web app!
echo =================================================================
python app.py
pause
