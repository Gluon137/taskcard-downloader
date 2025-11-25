# PowerShell Build Script for Taskcard Downloader (Windows)
# Run this script on a Windows machine to build the standalone app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Taskcard Downloader - Windows Builder" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running in venv
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
    } else {
        Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
        Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
        exit 1
    }
}

# Clean old builds
Write-Host "Cleaning old builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Build with PyInstaller
Write-Host "`nBuilding application with PyInstaller..." -ForegroundColor Yellow
pyinstaller --clean taskcard_downloader_windows.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Build successful!" -ForegroundColor Green

# Find and copy Chromium browser
Write-Host "`nSearching for Chromium browser..." -ForegroundColor Yellow

$playwrightCache = "$env:LOCALAPPDATA\ms-playwright"
if (-not (Test-Path $playwrightCache)) {
    Write-Host "WARNING: Playwright cache not found at: $playwrightCache" -ForegroundColor Red
    Write-Host "Please install Chromium with: playwright install chromium" -ForegroundColor Yellow
    exit 1
}

$chromiumDirs = Get-ChildItem $playwrightCache -Filter "chromium-*" -Directory
if ($chromiumDirs.Count -eq 0) {
    Write-Host "ERROR: No Chromium installation found!" -ForegroundColor Red
    Write-Host "Please run: playwright install chromium" -ForegroundColor Yellow
    exit 1
}

$chromiumPath = $chromiumDirs[0].FullName
Write-Host "Found Chromium at: $chromiumPath" -ForegroundColor Green

# Create playwright_browsers directory in dist
$targetDir = "dist\TaskcardDownloader\playwright_browsers"
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

# Copy Chromium
Write-Host "Copying Chromium browser (this may take a while)..." -ForegroundColor Yellow
$targetChromiumDir = Join-Path $targetDir $chromiumDirs[0].Name
Copy-Item -Recurse -Force $chromiumPath $targetChromiumDir

Write-Host "Chromium copied successfully!" -ForegroundColor Green

# Get sizes
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$distSize = (Get-ChildItem -Path "dist\TaskcardDownloader" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Total size: $([math]::Round($distSize, 2)) MB" -ForegroundColor Yellow

# Create zip archive
Write-Host "`nCreating distribution archive..." -ForegroundColor Yellow
$zipName = "TaskcardDownloader-Windows.zip"
Compress-Archive -Path "dist\TaskcardDownloader" -DestinationPath $zipName -Force

$zipSize = (Get-Item $zipName).Length / 1MB
Write-Host "Archive created: $zipName ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nOutput files:" -ForegroundColor Yellow
Write-Host "  - Folder: dist\TaskcardDownloader\" -ForegroundColor White
Write-Host "  - Archive: $zipName" -ForegroundColor White
Write-Host "`nTo test: .\dist\TaskcardDownloader\TaskcardDownloader.exe" -ForegroundColor Cyan
