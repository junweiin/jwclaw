# Open Application Script for Windows
# Usage: open_app.ps1 <AppName>

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

Write-Host "[OPEN] 尝试打开应用: $AppName"

# 常见应用映射表
$appMap = @{
    "chrome" = "chrome"
    "edge" = "msedge"
    "firefox" = "firefox"
    "code" = "code"
    "vscode" = "code"
    "notepad" = "notepad"
    "calc" = "calc"
    "explorer" = "explorer"
    "taskmgr" = "taskmgr"
    "cmd" = "cmd"
    "powershell" = "powershell"
    "terminal" = "wt"
    "word" = "WINWORD"
    "excel" = "EXCEL"
    "ppt" = "POWERPNT"
    "outlook" = "outlook"
    "mail" = "outlook"
    "photos" = "ms-photos:"
    "settings" = "ms-settings:"
    "store" = "ms-windows-store:"
}

# 检查是否是映射中的应用
$lowerName = $AppName.ToLower().Trim()
if ($appMap.ContainsKey($lowerName)) {
    $actualApp = $appMap[$lowerName]
    Write-Host "[INFO] 映射到: $actualApp"
    
    try {
        Start-Process $actualApp -ErrorAction Stop
        Write-Host "[OK] 成功打开: $AppName"
        exit 0
    } catch {
        Write-Host "[WARN] 启动失败: $_"
        Write-Host "[INFO] 尝试使用 start 命令..."
    }
}

# 如果不是映射应用，尝试直接执行
try {
    # 检查是否是完整路径
    if (Test-Path $AppName) {
        Write-Host "[INFO] 检测到文件路径，直接打开"
        Invoke-Item $AppName
        Write-Host "[OK] 成功打开: $AppName"
        exit 0
    }
    
    # 尝试使用 start 命令
    Write-Host "[INFO] 尝试使用 start 命令"
    Start-Process $AppName -ErrorAction Stop
    Write-Host "[OK] 成功打开: $AppName"
    exit 0
    
} catch {
    Write-Host "[ERROR] Cannot open application: $AppName"
    Write-Host ""
    Write-Host "Possible reasons:"
    Write-Host "  1. Application name is incorrect"
    Write-Host "  2. Application is not installed"
    Write-Host "  3. Path does not exist"
    Write-Host ""
    Write-Host "Suggestions:"
    Write-Host "  - Use full path, e.g.: C:\Program Files\App\app.exe"
    Write-Host "  - Use common app names: chrome, edge, code, notepad, calc"
    Write-Host "  - Or use shell directly: tool: shell(\"start appname\")"
    exit 1
}
