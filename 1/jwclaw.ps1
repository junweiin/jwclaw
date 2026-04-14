# JwClaw 智能体系统启动脚本 (PowerShell)
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  正在启动 JwClaw 智能体系统..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptPath\jwclaw.py" @args

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ JwClaw 启动失败" -ForegroundColor Red
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
