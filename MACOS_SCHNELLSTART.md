# Taskcard Downloader - macOS Schnellstart

## 🚀 Installation (2 Schritte)

### 1. ZIP-Datei entpacken
Entpacken Sie `TaskcardDownloader-macOS.zip` in einen beliebigen Ordner

### 2. App starten
Rechtsklick auf `TaskcardDownloader.app` → **"Öffnen"**

**Das war's!** Die App ist sofort einsatzbereit - kein Python, keine Installation nötig.

---

## 📥 Verwendung

1. Geben Sie Ihre Taskcard-URL ein (inkl. Token)
2. Wählen Sie einen Speicherort (Standard: `Dokumente/TaskCards/`)
3. Optional: Deaktivieren Sie "PDF-Anhänge integrieren" für schnelleren Download
4. Klicken Sie auf **"Download starten"**
5. Warten Sie 2-5 Minuten (je nach Anzahl der Anhänge)
6. Fertig! Die PDF-Datei wird automatisch gespeichert

---

## 🔒 macOS Sicherheitswarnung

### Problem: "App ist beschädigt und kann nicht geöffnet werden"

Diese Warnung erscheint, weil die App nicht von einem registrierten Apple Developer signiert ist.

#### Lösung 1: Rechtsklick-Menü (empfohlen)

1. **Rechtsklick** (oder Control+Klick) auf `TaskcardDownloader.app`
2. Wählen Sie **"Öffnen"** aus dem Menü
3. Klicken Sie im Dialog auf **"Öffnen"**
4. Die App startet nun und kann in Zukunft normal geöffnet werden

#### Lösung 2: Terminal-Befehl

Wenn Lösung 1 nicht funktioniert, öffnen Sie das Terminal und führen Sie aus:

```bash
xattr -cr /Pfad/zu/TaskcardDownloader.app
```

Ersetzen Sie `/Pfad/zu/` mit dem tatsächlichen Pfad zur App.

**Tipp:** Ziehen Sie die App einfach ins Terminal-Fenster, um den Pfad automatisch einzufügen.

#### Lösung 3: Systemeinstellungen

1. Öffnen Sie **Systemeinstellungen** → **Datenschutz & Sicherheit**
2. Scrollen Sie nach unten zu "Sicherheit"
3. Klicken Sie auf **"Trotzdem öffnen"** neben der TaskcardDownloader-Meldung

---

## ℹ️ Wichtige Hinweise

- **Kein Python erforderlich** - Die App funktioniert eigenständig
- **Chromium Browser eingebettet** - Alles ist bereits enthalten (ca. 560 MB)
- **Internet erforderlich** - Nur zum Download der Taskcard-Inhalte
- **Speicherort der Dateien** - Standard: `~/Documents/TaskCards/`
- **Portabel** - Der gesamte Ordner kann auf USB-Stick kopiert werden
- **Copy-Paste funktioniert** - Cmd+V zum Einfügen von URLs

---

## 🆘 Probleme?

**App startet nicht?**
→ Prüfen Sie, ob alle Dateien entpackt wurden (besonders der `playwright_browsers` Ordner)

**Download schlägt fehl?**
→ Taskcard-URL überprüfen (muss Token enthalten)

**"playwright_browsers not found"?**
→ Stellen Sie sicher, dass der Ordner `playwright_browsers` in der App enthalten ist

**Timeout-Fehler bei PDFs?**
→ Normal bei großen Dateien - die App lädt alle verfügbaren PDFs herunter

---

## 📁 Ordnerstruktur

```
TaskcardDownloader.app/
├── Contents/
│   ├── MacOS/
│   │   └── TaskcardDownloader          # Hauptprogramm
│   ├── Resources/
│   │   ├── playwright_browsers/        # Chromium Browser (~420 MB)
│   │   │   └── chromium-1140/
│   │   └── _internal/                  # Python-Bibliotheken
│   └── Info.plist
```

---

## 💾 Systemanforderungen

- **Betriebssystem**: macOS 11 Big Sur oder neuer (Apple Silicon & Intel)
- **Arbeitsspeicher**: Min. 2 GB RAM (empfohlen: 4 GB)
- **Festplatte**: Min. 700 MB freier Speicherplatz
- **Internet**: Erforderlich für Download

---

## 🗑️ Deinstallation

Einfach die App `TaskcardDownloader.app` in den Papierkorb ziehen - fertig!

Optional: Heruntergeladene PDFs löschen:
`~/Documents/TaskCards/`

---

## 🔐 Sicherheit

Die App ist sicher und enthält keine Malware. Die Warnung "App ist beschädigt" ist Standard bei nicht signierten Apps.

**Warum ist die App nicht signiert?**
Apple Developer Signierung kostet 99$/Jahr. Da dies ein Open-Source Projekt ist, verwenden wir Ad-hoc Signierung.

**Kann ich den Quellcode prüfen?**
Ja! Der gesamte Quellcode ist auf GitHub verfügbar: https://github.com/[Ihr-Repository]
