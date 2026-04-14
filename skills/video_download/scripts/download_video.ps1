# Video Download Script for Windows
# Usage: download_video.ps1 <URL> [OutputDir]

param(
    [Parameter(Mandatory=$true)]
    [string]$Url,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir
)

# Set default output directory if not provided
if (-not $OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "..\..\..\downloads"
    $OutputDir = Resolve-Path $OutputDir -ErrorAction SilentlyContinue
    if (-not $OutputDir) {
        $OutputDir = "C:\Users\jw\Desktop\agent\downloads"
    }
}

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Starting video download..."
Write-Host "URL: $Url"
Write-Host "Output: $OutputDir"
Write-Host ""

# Check if yt-dlp is available
$ytDlpCmd = $null
try {
    $null = Get-Command yt-dlp -ErrorAction Stop
    $ytDlpCmd = "yt-dlp"
    Write-Host "[OK] Found yt-dlp command"
} catch {
    try {
        python -m yt_dlp --version | Out-Null
        $ytDlpCmd = "python -m yt_dlp"
        Write-Host "[OK] Found python -m yt_dlp"
    } catch {
        Write-Host "[ERROR] yt-dlp not found, installing..."
        python -m pip install -q yt-dlp
        if ($LASTEXITCODE -eq 0) {
            $ytDlpCmd = "python -m yt_dlp"
            Write-Host "[OK] yt-dlp installed successfully"
        } else {
            Write-Host "[ERROR] Failed to install yt-dlp"
            exit 1
        }
    }
}

Write-Host ""
Write-Host "Downloading video, please wait..."
Write-Host "Tip: Large files may take several minutes"
Write-Host ""

# Try downloading with merge first
if ($ytDlpCmd -eq "python -m yt_dlp") {
    $result = python -m yt_dlp $Url `
        -o "$OutputDir\%(title)s.%(ext)s" `
        --merge-output-format mp4 `
        --no-playlist `
        --no-check-certificates `
        --socket-timeout 30 `
        2>&1
} else {
    $result = & $ytDlpCmd $Url `
        -o "$OutputDir\%(title)s.%(ext)s" `
        --merge-output-format mp4 `
        --no-playlist `
        --no-check-certificates `
        --socket-timeout 30 `
        2>&1
}

$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[WARN] Merge failed, trying separate download..."
    
    # Try without merge
    if ($ytDlpCmd -eq "python -m yt_dlp") {
        $result = python -m yt_dlp $Url `
            -o "$OutputDir\%(title)s.%(ext)s" `
            --no-playlist `
            --no-check-certificates `
            --socket-timeout 30 `
            2>&1
    } else {
        $result = & $ytDlpCmd $Url `
            -o "$OutputDir\%(title)s.%(ext)s" `
            --no-playlist `
            --no-check-certificates `
            --socket-timeout 30 `
            2>&1
    }
    
    $exitCode = $LASTEXITCODE
}

# Output result
$result | ForEach-Object { Write-Host $_ }

Write-Host ""

# Check downloaded files
$recentFiles = Get-ChildItem $OutputDir -File | 
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) } | 
    Sort-Object LastWriteTime -Descending

if ($recentFiles.Count -eq 0) {
    Write-Host "[FAIL] Download failed, no files found"
    Write-Host ""
    Write-Host "Possible reasons:"
    Write-Host "  1. Network connection issue"
    Write-Host "  2. Invalid video URL or requires login"
    Write-Host "  3. Platform restrictions"
    Write-Host ""
    Write-Host "Suggestion: Check network and retry"
    exit 1
} elseif ($recentFiles.Count -eq 1 -and $recentFiles[0].Extension -eq '.mp4') {
    $sizeMB = [math]::Round($recentFiles[0].Length / 1MB, 1)
    Write-Host "[SUCCESS] Downloaded: $($recentFiles[0].Name) (${sizeMB}MB)"
    Write-Host "Location: $($recentFiles[0].FullName)"
} elseif ($recentFiles.Count -ge 2) {
    # Multiple files (audio and video separated)
    $totalSize = ($recentFiles | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($totalSize / 1MB, 1)
    
    Write-Host "[SUCCESS] Downloaded (separate audio/video):"
    foreach ($f in $recentFiles) {
        $fSize = [math]::Round($f.Length / 1MB, 1)
        Write-Host "  - $($f.Name) (${fSize}MB)"
    }
    Write-Host ""
    Write-Host "Total size: ${sizeMB}MB"
    Write-Host ""
    Write-Host "TIP: To merge into MP4, install ffmpeg and retry:"
    Write-Host "   Option 1 (Recommended): winget install Gyan.FFmpeg"
    Write-Host "   Option 2 (China mirror): https://www.gyan.dev/ffmpeg/builds/"
    Write-Host "   After installation, re-run the download command to auto-merge"
} else {
    Write-Host "[WARN] Unknown state, check Downloads directory"
}
