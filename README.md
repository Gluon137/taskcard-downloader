# Taskcard Downloader

Eine Stand-Alone-Anwendung zum vollständigen Download von Taskcard-Boards als PDF-Datei, inklusive aller Karten-Inhalte und PDF-Anhänge.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- 📥 **Vollständiger Board-Download** - Alle Spalten, Karten und Inhalte
- 📎 **PDF-Integration** - Automatische Integration aller angehängten PDF-Dateien
- 🖥️ **Stand-Alone** - Keine Python-Installation erforderlich (für Windows/macOS Builds)
- 🌐 **Cross-Platform** - Verfügbar für macOS, Windows und als Python-Script
- 🎨 **Benutzerfreundliche GUI** - Einfache grafische Oberfläche
- 🔧 **CLI-Option** - Auch per Kommandozeile verwendbar
- 🔒 **Offline-fähig** - Nach dem Download keine Internetverbindung nötig

## 📦 Download (Stand-Alone Versionen)

### Aktuelle Version

Laden Sie die neueste Version für Ihr Betriebssystem herunter - keine Python-Installation erforderlich:

- **macOS**: [TaskcardDownloader.app](../../releases/latest) (~560 MB)
- **Windows**: [TaskcardDownloader.exe](../../releases/latest) (~560 MB)

### Schnellstart für Stand-Alone Versionen

**macOS:**
1. ZIP entpacken → Rechtsklick auf App → "Öffnen" → Fertig!

**Windows:**
1. ZIP entpacken → .exe starten → Bei SmartScreen: "Weitere Informationen" → "Trotzdem ausführen" → Fertig!

## 🛠️ Python-Installation (für Entwickler)

Wenn Sie das Tool aus dem Quellcode verwenden möchten:

### 1. Virtuelle Umgebung erstellen (empfohlen)

```bash
python3 -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

### 2. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Playwright-Browser installieren

```bash
playwright install chromium
```

## Verwendung

### Grundlegende Nutzung

```bash
python taskcard_downloader.py "https://bra.taskcards.app/#/board/BOARD-ID?token=TOKEN"
```

### Mit eigenem Dateinamen

```bash
python taskcard_downloader.py "https://bra.taskcards.app/#/board/BOARD-ID?token=TOKEN" -o meine_taskcard.pdf
```

### Beispiel mit deiner Taskcard

```bash
python taskcard_downloader.py "https://bra.taskcards.app/#/board/4d8b2251-c68e-471a-80f9-d4a30e1d14c8?token=e6a9dbfd-0488-4763-81dd-c3bc380ef2d6"
```

## Ausgabe

Das generierte PDF enthält:

1. **Übersichtsteil:**
   - Board-Titel (zentriert, blau)
   - Erstellungsdatum
   - Für jede Spalte:
     - Spaltentitel (grün, mit ▶ Symbol)
     - Alle Karten in dieser Spalte:
       - Kartentitel (rot, mit ● Symbol)
       - Karteninhalt/Beschreibung
       - Anhänge (grau, mit 📎 Symbol, inkl. Dateityp und Größe)
       - Links (blau, anklickbar, mit 🔗 Symbol)

2. **Angehängte PDFs:**
   - Alle PDF-Anhänge werden vollständig in das Dokument integriert
   - Jedes PDF behält seine ursprüngliche Formatierung

## Optionen

```
usage: taskcard_downloader.py [-h] [-o OUTPUT] [--no-attachments] url

positional arguments:
  url                   Taskcard URL (including token)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output PDF filename (default: taskcard_YYYYMMDD_HHMMSS.pdf)
  --no-attachments      Do not include PDF attachments in the output (nur Übersicht)
```

### Beispiele

**Mit allen PDF-Anhängen (Standard):**
```bash
python taskcard_downloader.py "YOUR_URL" -o complete.pdf
```

**Nur Übersicht ohne Anhänge:**
```bash
python taskcard_downloader.py "YOUR_URL" --no-attachments -o overview_only.pdf
```

## Systemanforderungen

- Python 3.8 oder höher
- Internet-Verbindung
- Ca. 200 MB Speicherplatz für Playwright-Browser

## Hinweise

- **Download-Dauer:** Das Herunterladen der PDF-Anhänge kann je nach Anzahl und Größe 2-5 Minuten dauern
- **Dateigröße:** Das finale PDF kann sehr groß werden (z.B. 45 MB bei 31 integrierten PDFs)
- **Timeout:** Einzelne PDFs können bei Timeout-Problemen übersprungen werden (wird angezeigt)

## Debugging

Das Script erstellt automatisch einen Screenshot (`taskcard_debug.png`) der geladenen Seite. Dies kann hilfreich sein, um zu überprüfen, ob die Seite korrekt geladen wurde.

## Fehlerbehebung

### "Browser not found"
Stelle sicher, dass du `playwright install chromium` ausgeführt hast.

### "ModuleNotFoundError: No module named 'playwright'"
Stelle sicher, dass du die virtuelle Umgebung aktiviert hast:
```bash
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

### Wenige oder keine Spalten gefunden
- Prüfe, ob die Taskcard-URL korrekt ist (inkl. Token)
- Prüfe den erstellten Screenshot `taskcard_debug.png`
- Erhöhe ggf. die Wartezeit in Zeile 42 der .py-Datei (aktuell 5000ms)

### Timeout-Fehler
Bei langsamer Internetverbindung kann das Timeout erhöht werden (in Zeile 39 der .py-Datei, aktuell 30000ms).

## Lizenz

Freie Verwendung für persönliche und kommerzielle Zwecke.
