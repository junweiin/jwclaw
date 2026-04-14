@echo off
REM JwClaw 智能体系统启动脚本
chcp 65001 >nul
echo.
echo ========================================
echo   正在启动 JwClaw 智能体系统...
echo ========================================
echo.

python "%~dp0jwclaw.py" %*

if errorlevel 1 (
    echo.
    echo ❌ JwClaw 启动失败
    pause
)
