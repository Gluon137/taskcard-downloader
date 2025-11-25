# Taskcard Downloader - Stand-Alone App

Diese Stand-Alone-Version funktioniert auf jedem Mac **ohne Python-Installation**.

## Installation auf einem neuen Mac

### Schritt 1: App kopieren
Kopieren Sie die Datei `TaskcardDownloader.app` auf den Ziel-Mac (z.B. via USB-Stick, AirDrop, etc.)

Optional: Kopieren Sie die App in den Programme-Ordner:
```bash
cp -r TaskcardDownloader.app /Applications/
```

### Schritt 2: App starten

Bei der ersten Ausführung erscheint eine Sicherheitswarnung von macOS:

1. **Rechtsklick** auf `TaskcardDownloader.app` → **Öffnen**
2. Klicken Sie auf **"Öffnen"** in der Warnung

Oder:
1. Versuchen Sie die App zu öffnen (Doppelklick)
2. Gehen Sie zu **Systemeinstellungen** → **Datenschutz & Sicherheit**
3. Klicken Sie auf **"Dennoch öffnen"**

### Schritt 3: Browser-Installation (automatisch)

Beim **ersten Start** der App wird automatisch ein Dialog erscheinen, der Sie auffordert, die erforderlichen Browser zu installieren (~140 MB Download).

1. Klicken Sie auf **"Browser jetzt installieren"**
2. Warten Sie, bis der Download abgeschlossen ist (2-3 Minuten)
3. Fertig! Die App ist jetzt einsatzbereit

**Wichtig:** Diese Installation ist nur **einmal** notwendig. Danach startet die App normal.

## Verwendung

1. Öffnen Sie die App
2. Geben Sie die Taskcard-URL ein (mit Token)
3. Wählen Sie den Ausgabe-Speicherort (Standard: `~/Documents/TaskCards/`)
4. Optional: Deaktivieren Sie "PDF-Anhänge integrieren" für schnelleren Download
5. Klicken Sie auf "Download starten"

## Dateien werden gespeichert in:
- Standard: `~/Documents/TaskCards/`
- Der Ordner wird automatisch erstellt
- Dateinamen enthalten Zeitstempel: `taskcard_20251123_143022.pdf`

## Technische Details

### Browser-Speicherort
Die Playwright-Browser werden hier gespeichert:
```
~/.taskcard_downloader/playwright_browsers/
```

Dieser Ordner ist ca. 140 MB groß und wird nur einmal heruntergeladen.

### Fehlerbehebung

**Problem: Browser-Installation schlägt fehl**
- Stellen Sie sicher, dass eine Internetverbindung besteht
- Starten Sie die App neu - der Installations-Dialog erscheint erneut
- Prüfen Sie, ob genügend Speicherplatz vorhanden ist (~140 MB)

**Problem: "Permission denied"**
- Machen Sie die App ausführbar:
  ```bash
  chmod +x TaskcardDownloader.app/Contents/MacOS/TaskcardDownloader
  ```

**Problem: App wird von macOS blockiert**
- Siehe Schritt 2 oben (Rechtsklick → Öffnen)
- Die App ist nicht signiert, daher erscheint diese Warnung

## Deinstallation

Um die App vollständig zu entfernen:
```bash
# App löschen
rm -rf /Applications/TaskcardDownloader.app

# Browser-Daten löschen (ca. 140 MB)
rm -rf ~/.taskcard_downloader
```

## Support

Bei Problemen:
1. Überprüfen Sie, ob die Browser installiert sind
2. Schauen Sie in das Status-Log in der App
3. Prüfen Sie Ihre Internetverbindung
