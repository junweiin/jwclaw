---
name: video_download
description: 智能下载网络视频，支持Bilibili、YouTube等平台
---

## 描述
**智能下载网络视频**。自动检测并安装所需工具（yt-dlp、ffmpeg），支持Bilibili、YouTube、抖音等主流平台。

**重要：当用户要求下载视频时，必须使用此skill！**




## 调用格式
tool: video_download("视频URL", "输出目录(可选)")

## 命令列表
| 命令 | 说明 | 参数 |
|------|------|------|
| download_video | 下载视频 | URL [输出目录] |

## 前置条件
```bash
pip install yt-dlp
winget install Gyan.FFmpeg
```

## 执行流程

### Step 1：检查并安装yt-dlp
```powershell
# 检查yt-dlp是否可用
$ytDlpAvailable = $false
try {
    $null = Get-Command yt-dlp -ErrorAction Stop
    $ytDlpAvailable = $true
} catch {
    try {
        python -m yt_dlp --version | Out-Null
        $ytDlpAvailable = $true
    } catch {
        $ytDlpAvailable = $false
    }
}

if (-not $ytDlpAvailable) {
    Write-Host "📦 正在安装yt-dlp..."
    python -m pip install -q yt-dlp
    Write-Host "✅ yt-dlp安装完成"
} else {
    Write-Host "✅ yt-dlp已就绪"
}
```

### Step 2：尝试下载（优先合并）
```powershell
Write-Host "`n📥 正在下载视频，请稍候..."
Write-Host "💡 提示: 大文件可能需要几分钟时间`n"

# 尝试使用yt-dlp命令
$cmd = "yt-dlp"
try {
    $null = Get-Command yt-dlp -ErrorAction Stop
} catch {
    $cmd = "python -m yt_dlp"
}

$result = & $cmd "{url}" -o "{output_dir}\%(title)s.%(ext)s" --merge-output-format mp4 --no-playlist --no-check-certificates 2>&1

if ($LASTEXITCODE -ne 0) {
    # 如果合并失败，尝试不合并下载
    Write-Host "`n⚠️  合并失败，尝试分开下载音视频..."
    $result = & $cmd "{url}" -o "{output_dir}\%(title)s.%(ext)s" --no-playlist --no-check-certificates 2>&1
}

$result
```

### Step 3：检查结果并提供建议
```powershell
$files = Get-ChildItem "{output_dir}" -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) } | Sort-Object LastWriteTime -Descending

if ($files.Count -eq 0) {
    "❌ 下载失败，未找到文件`n`n可能原因:`n  1. 网络连接问题`n  2. 视频链接无效或需要登录`n  3. B站限制了下载`n`n建议: 请检查网络连接后重试"
} elseif ($files.Count -eq 1 -and $files[0].Extension -eq '.mp4') {
    $sizeMB = [math]::Round($files[0].Length / 1MB, 1)
    "✅ 下载成功: $($files[0].Name) ($sizeMB MB)"
} elseif ($files.Count -ge 2) {
    # 有多个文件，说明音视频分开了
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($totalSize / 1MB, 1)
    
    $msg = "✅ 下载成功（音视频分离）:`n"
    foreach ($f in $files) {
        $fSize = [math]::Round($f.Length / 1MB, 1)
        $msg += "  - $($f.Name) ($fSize MB)`n"
    }
    $msg += "`n总大小: $sizeMB MB`n`n"
    $msg += "💡 提示: 如需合并为MP4，请安装ffmpeg后重试：`n"
    $msg += "   方法1（推荐）: winget install Gyan.FFmpeg`n"
    $msg += "   方法2（国内镜像）: https://www.gyan.dev/ffmpeg/builds/`n"
    $msg += "   安装后重新执行下载命令即可自动合并"
    $msg
} else {
    "⚠️  未知状态，请检查Downloads目录"
}
```
