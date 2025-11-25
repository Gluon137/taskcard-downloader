#!/usr/bin/env python3
"""
Browser Installer for Taskcard Downloader
Installiert Playwright-Browser beim ersten Start
"""

import os
import sys
import subprocess
from pathlib import Path

# Set the same browser path as in taskcard_downloader.py
BROWSERS_PATH = Path.home() / ".taskcard_downloader" / "playwright_browsers"
BROWSERS_PATH.mkdir(parents=True, exist_ok=True)

def install_browsers():
    """Install Playwright browsers"""
    print("\n" + "="*70)
    print("Taskcard Downloader - Browser Installation")
    print("="*70)
    print(f"\nBrowser werden installiert nach: {BROWSERS_PATH}")
    print("\nDies kann einige Minuten dauern...")
    print("="*70 + "\n")

    # Set environment variable
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(BROWSERS_PATH)

    try:
        # Try to install using playwright command
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )

        print(result.stdout)

        print("\n" + "="*70)
        print("✅ Browser erfolgreich installiert!")
        print("="*70 + "\n")
        print("Sie können jetzt die Taskcard Downloader App verwenden.\n")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fehler bei der Installation: {e}")
        print(f"\nStdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        print("\nBitte installieren Sie Playwright manuell:")
        print(f"  PLAYWRIGHT_BROWSERS_PATH={BROWSERS_PATH} playwright install chromium\n")
        return False

    except FileNotFoundError:
        print("\n❌ Playwright ist nicht installiert.")
        print("\nBitte installieren Sie zuerst die Abhängigkeiten:")
        print("  pip install playwright")
        print(f"  PLAYWRIGHT_BROWSERS_PATH={BROWSERS_PATH} playwright install chromium\n")
        return False


if __name__ == "__main__":
    success = install_browsers()
    sys.exit(0 if success else 1)
