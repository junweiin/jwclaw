@echo off
chcp 65001 >nul
echo ========================================
echo   正在启动 JwClaw Web UI...
echo ========================================
echo.

python jwclaw.py --gui

pause
