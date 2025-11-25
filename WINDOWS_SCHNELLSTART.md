# Taskcard Downloader - Windows Schnellstart

## 🚀 Installation (2 Schritte)

### 1. ZIP-Datei entpacken
Entpacken Sie `TaskcardDownloader-Windows.zip` in einen beliebigen Ordner

### 2. App starten
Doppelklick auf `TaskcardDownloader.exe` im entpackten Ordner

**Das war's!** Die App ist sofort einsatzbereit - kein Python, keine Installation nötig.

---

## 📥 Verwendung

1. Geben Sie Ihre Taskcard-URL ein (inkl. Token)
2. Wählen Sie einen Speicherort (Standard: `Dokumente\TaskCards\`)
3. Optional: Deaktivieren Sie "PDF-Anhänge integrieren" für schnelleren Download
4. Klicken Sie auf **"Download starten"**
5. Warten Sie 2-5 Minuten (je nach Anzahl der Anhänge)
6. Fertig! Die PDF-Datei wird automatisch gespeichert

---

## ℹ️ Wichtige Hinweise

- **Kein Python erforderlich** - Die App funktioniert eigenständig
- **Chromium Browser eingebettet** - Alles ist bereits enthalten (ca. 560 MB)
- **Internet erforderlich** - Nur zum Download der Taskcard-Inhalte
- **Speicherort der Dateien** - Standard: `C:\Users\<Username>\Documents\TaskCards\`
- **Portabel** - Der gesamte Ordner kann auf USB-Stick kopiert werden

---

## 🔒 Windows Sicherheitswarnung

Beim ersten Start erscheint möglicherweise eine SmartScreen-Warnung:

**"Windows hat den Start dieser App verhindert"**

1. Klicken Sie auf **"Weitere Informationen"**
2. Klicken Sie auf **"Trotzdem ausführen"**

Die App ist sicher - die Warnung erscheint, weil die App nicht signiert ist.

---

## 🆘 Probleme?

**App startet nicht?**
→ Prüfen Sie, ob alle Dateien entpackt wurden (besonders der `playwright_browsers` Ordner)

**Download schlägt fehl?**
→ Taskcard-URL überprüfen (muss Token enthalten)

**"playwright_browsers not found"?**
→ Stellen Sie sicher, dass der Ordner `playwright_browsers` neben der .exe liegt

---

## 📁 Ordnerstruktur

```
TaskcardDownloader/
├── TaskcardDownloader.exe          # Hauptprogramm
├── playwright_browsers/             # Chromium Browser (~420 MB)
│   └── chromium-1140/
├── _internal/                       # Python-Bibliotheken
└── (weitere DLL-Dateien)
```

---

## 💾 Systemanforderungen

- **Betriebssystem**: Windows 10/11 (64-bit)
- **Arbeitsspeicher**: Min. 2 GB RAM (empfohlen: 4 GB)
- **Festplatte**: Min. 700 MB freier Speicherplatz
- **Internet**: Erforderlich für Download

---

## 🗑️ Deinstallation

Einfach den Ordner `TaskcardDownloader` löschen - fertig!

Optional: Heruntergeladene PDFs löschen:
`C:\Users\<Username>\Documents\TaskCards\`
