# Windows Build-Anleitung für Taskcard Downloader

Diese Anleitung erklärt, wie Sie die Windows-Version der Taskcard Downloader App erstellen.

## Voraussetzungen

- Windows 10/11
- Python 3.9 oder höher
- Git (optional, zum Klonen des Projekts)

## Schritt-für-Schritt Anleitung

### 1. Projekt vorbereiten

Kopieren Sie alle Projektdateien auf Ihren Windows-Computer:
- `taskcard_downloader.py`
- `taskcard_downloader_gui.py`
- `requirements.txt`
- `taskcard_downloader_windows.spec` (wird unten erstellt)

### 2. Virtuelle Umgebung erstellen

Öffnen Sie PowerShell oder CMD im Projektordner:

```powershell
# Virtuelle Umgebung erstellen
python -m venv venv

# Aktivieren
.\venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
pip install pyinstaller
```

### 3. Playwright Browser installieren

```powershell
# Browser installieren
playwright install chromium

# Browser-Pfad prüfen
dir %USERPROFILE%\.cache\ms-playwright\chromium-*
```

Der Browser wird normalerweise hier installiert:
`C:\Users\<Username>\AppData\Local\ms-playwright\chromium-<version>`

### 4. PyInstaller Spec-Datei für Windows

Erstellen Sie die Datei `taskcard_downloader_windows.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

block_cipher = None

# Note: Chromium will be copied manually after build
datas = []

a = Analysis(
    ['taskcard_downloader_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'playwright',
        'playwright.async_api',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.platypus',
        'PyPDF2',
        'requests',
        'tkinter',
        'asyncio',
        'tempfile',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaskcardDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optional: Add .ico file here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TaskcardDownloader',
)
```

### 5. App kompilieren

```powershell
# Alte Builds löschen
rmdir /s /q dist
rmdir /s /q build

# Neu kompilieren
pyinstaller taskcard_downloader_windows.spec
```

### 6. Chromium Browser in die App kopieren

```powershell
# Browser-Verzeichnis finden
$chromiumPath = Get-ChildItem "$env:LOCALAPPDATA\ms-playwright" -Filter "chromium-*" -Directory | Select-Object -First 1

# In dist-Ordner kopieren
mkdir "dist\TaskcardDownloader\playwright_browsers"
Copy-Item -Recurse "$chromiumPath\*" "dist\TaskcardDownloader\playwright_browsers\$($chromiumPath.Name)"
```

### 7. App testen

```powershell
# App starten
.\dist\TaskcardDownloader\TaskcardDownloader.exe
```

### 8. Distribution vorbereiten

Die fertige App befindet sich in: `dist\TaskcardDownloader\`

Optionen:
- **Als Ordner verteilen**: Zip-Datei erstellen: `Compress-Archive -Path dist\TaskcardDownloader -DestinationPath TaskcardDownloader-Windows.zip`
- **Installer erstellen**: Mit Tools wie Inno Setup oder NSIS

## Erwartete Größe

- Ohne Browser: ~100-150 MB
- Mit Browser: ~500-600 MB

## Fehlerbehebung

### Problem: "playwright not found"
```powershell
pip install playwright
playwright install chromium
```

### Problem: "tkinter not found"
- Tkinter sollte mit Python mitgeliefert werden
- Neuinstallation von Python mit "tcl/tk" Option

### Problem: Browser wird nicht gefunden
- Prüfen Sie, ob Chromium korrekt kopiert wurde
- Pfad prüfen: `dist\TaskcardDownloader\playwright_browsers\chromium-*`

### Problem: App startet nicht
- Testen Sie mit Console-Modus: In spec-Datei `console=True` setzen
- Fehlermeldungen im Terminal lesen

## Code-Anpassungen für Windows

Die Datei `taskcard_downloader.py` muss für Windows angepasst werden:

```python
def get_browsers_path():
    """Get the path to Playwright browsers, checking bundled resources first"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        if sys.platform == 'win32':  # Windows
            # For Windows executable, browsers are next to the .exe
            exe_path = Path(sys.executable)
            bundled_browsers = exe_path.parent / "playwright_browsers"

            if bundled_browsers.exists():
                print(f"Using bundled browsers from: {bundled_browsers}")
                return bundled_browsers

        elif sys.platform == 'darwin':  # macOS
            # For .app bundle, browsers are in Contents/Resources
            exe_path = Path(sys.executable)
            app_resources = exe_path.parent.parent / "Resources" / "playwright_browsers"

            if app_resources.exists():
                print(f"Using bundled browsers from: {app_resources}")
                return app_resources

        # Check _MEIPASS (for onedir builds)
        bundle_dir = Path(sys._MEIPASS)
        bundled_browsers = bundle_dir / "playwright_browsers"
        if bundled_browsers.exists():
            print(f"Using bundled browsers from: {bundled_browsers}")
            return bundled_browsers

    # Fall back to user's home directory
    if sys.platform == 'win32':
        user_browsers = Path.home() / "AppData" / "Local" / "taskcard_downloader" / "playwright_browsers"
    else:
        user_browsers = Path.home() / ".taskcard_downloader" / "playwright_browsers"

    user_browsers.mkdir(parents=True, exist_ok=True)
    return user_browsers
```

## Automatisiertes Build-Script

Erstellen Sie `build_windows.ps1`:

```powershell
# Build script for Windows
Write-Host "Building Taskcard Downloader for Windows..." -ForegroundColor Green

# Activate venv
.\venv\Scripts\activate

# Clean old builds
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Build
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
pyinstaller taskcard_downloader_windows.spec

# Copy Chromium
Write-Host "Copying Chromium browser..." -ForegroundColor Yellow
$chromiumPath = Get-ChildItem "$env:LOCALAPPDATA\ms-playwright" -Filter "chromium-*" -Directory | Select-Object -First 1

if ($chromiumPath) {
    New-Item -ItemType Directory -Force -Path "dist\TaskcardDownloader\playwright_browsers"
    Copy-Item -Recurse "$chromiumPath\*" "dist\TaskcardDownloader\playwright_browsers\$($chromiumPath.Name)"
    Write-Host "Browser copied successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Chromium not found! Please run 'playwright install chromium'" -ForegroundColor Red
    exit 1
}

# Create zip
Write-Host "Creating distribution package..." -ForegroundColor Yellow
Compress-Archive -Path dist\TaskcardDownloader -DestinationPath TaskcardDownloader-Windows.zip -Force

Write-Host "Build complete! Package: TaskcardDownloader-Windows.zip" -ForegroundColor Green
Write-Host "Size:" -ForegroundColor Yellow
Get-Item TaskcardDownloader-Windows.zip | Select-Object Name, @{Name="Size (MB)";Expression={[math]::Round($_.Length / 1MB, 2)}}
```

Ausführen mit: `.\build_windows.ps1`

## Support

Bei Problemen:
1. Prüfen Sie die Python-Version: `python --version`
2. Prüfen Sie die Playwright-Installation: `playwright --version`
3. Testen Sie die App im Entwicklungsmodus: `python taskcard_downloader_gui.py`
