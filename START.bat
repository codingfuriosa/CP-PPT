@echo off
cd /d "%~dp0"
echo Starting Limitless Success... keep this window open while presenting.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve.ps1"
pause
