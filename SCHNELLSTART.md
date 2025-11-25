# Taskcard Downloader - Schnellstart

## 🚀 Installation in 3 Schritten

### 1. App kopieren
Übertragen Sie `TaskcardDownloader.app` auf Ihren Mac (via AirDrop, USB-Stick, etc.)

### 2. App öffnen
- **Rechtsklick** auf die App → **"Öffnen"**
- Bestätigen Sie die Sicherheitswarnung mit **"Öffnen"**

### 3. Browser installieren (nur beim ersten Mal)
- Ein Dialog erscheint automatisch
- Klicken Sie auf **"Browser jetzt installieren"**
- Warten Sie 2-3 Minuten
- Fertig!

---

## 📥 Verwendung

1. Geben Sie Ihre Taskcard-URL ein (inkl. Token)
2. Wählen Sie einen Speicherort (Standard: `~/Documents/TaskCards/`)
3. Optional: Deaktivieren Sie "PDF-Anhänge integrieren" für schnelleren Download
4. Klicken Sie auf **"Download starten"**
5. Warten Sie 2-5 Minuten (je nach Anzahl der Anhänge)
6. Fertig! Die PDF-Datei wird automatisch gespeichert

---

## ℹ️ Wichtige Hinweise

- **Kein Python erforderlich** - Die App funktioniert eigenständig
- **Einmalige Browser-Installation** - Nur beim ersten Start nötig (~140 MB)
- **Internet erforderlich** - Sowohl für Browser-Installation als auch Download
- **Speicherort der Dateien** - Standard: `~/Documents/TaskCards/`
- **Speicherort der Browser** - `~/.taskcard_downloader/playwright_browsers/`

---

## 🆘 Probleme?

**App startet nicht?**
→ Rechtsklick → "Öffnen" (nicht Doppelklick!)

**Browser-Installation schlägt fehl?**
→ Internetverbindung prüfen und App neu starten

**Download schlägt fehl?**
→ Taskcard-URL überprüfen (muss Token enthalten)

---

## 🗑️ Deinstallation

App löschen:
```bash
rm -rf /Applications/TaskcardDownloader.app
```

Browser-Daten löschen:
```bash
rm -rf ~/.taskcard_downloader
```
