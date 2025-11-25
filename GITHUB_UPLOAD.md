# GitHub Upload Anleitung

So laden Sie das Projekt auf GitHub hoch:

## 1. GitHub Repository erstellen

1. Gehen Sie zu [github.com](https://github.com) und melden Sie sich an
2. Klicken Sie auf das **"+"** Symbol oben rechts → **"New repository"**
3. Repository-Name: `taskcard-downloader` (oder Ihren Wunschnamen)
4. Beschreibung: "Download Taskcard boards as PDF with all attachments"
5. **Public** oder **Private** wählen
6. **NICHT** "Initialize with README" anklicken (haben wir schon!)
7. Klicken Sie auf **"Create repository"**

## 2. Repository verknüpfen und hochladen

Auf Ihrem Mac im Terminal (im Projektordner):

```bash
# GitHub Remote hinzufügen (ersetzen Sie USERNAME mit Ihrem GitHub-Benutzernamen)
git remote add origin https://github.com/USERNAME/taskcard-downloader.git

# Code hochladen
git push -u origin main
```

Falls Sie nach Anmeldedaten gefragt werden:
- **Username**: Ihr GitHub-Benutzername
- **Password**: Personal Access Token (NICHT Ihr Passwort!)

### Personal Access Token erstellen (falls nötig):

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. Häkchen bei **"repo"**
4. Token generieren und kopieren (nur einmal sichtbar!)
5. Als Passwort beim `git push` verwenden

## 3. Automatische Builds aktivieren

Die GitHub Actions sind bereits konfiguriert! Nach dem Push:

1. Gehen Sie zu Ihrem Repository auf GitHub
2. Klicken Sie auf den Tab **"Actions"**
3. Der erste Build startet automatisch
4. Warten Sie ~10-15 Minuten

Die Builds erstellen automatisch:
- macOS Version
- Windows Version

## 4. Release erstellen (optional)

Um eine Release-Version mit Downloads zu erstellen:

```bash
# Tag erstellen
git tag -a v1.0.0 -m "First release"

# Tag hochladen
git push origin v1.0.0
```

GitHub Actions erstellt dann automatisch ein Release mit beiden Apps!

## 5. Repository-Einstellungen (empfohlen)

### Topics hinzufügen:

1. Repository-Hauptseite → "Add topics"
2. Vorschläge: `taskcard`, `pdf-generator`, `python`, `playwright`, `macos`, `windows`

### About-Sektion:

1. Repository-Hauptseite → Zahnrad bei "About"
2. Beschreibung: "Download TaskCards boards as PDF with all attachments - Stand-alone apps for macOS and Windows"
3. Website: (optional)
4. Topics: Wie oben

### GitHub Pages (optional):

Falls Sie eine Webseite möchten:
1. Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: main → /docs (oder /root)

## 6. .gitignore anpassen (wichtig!)

Stellen Sie sicher, dass große Dateien NICHT hochgeladen werden:

```bash
# Diese Ordner sollten NICHT auf GitHub landen:
dist/                           # Zu groß (560 MB!)
build/                          # Build-Artefakte
venv/                          # Python Virtual Environment
__pycache__/                   # Python Cache
*.pyc                          # Compiled Python
.DS_Store                      # macOS
taskcard_debug.png            # Debug-Screenshots
*.pdf                          # Generated PDFs
```

**WICHTIG:** Der `dist/` Ordner ist zu groß für GitHub! Löschen Sie ihn vor dem Upload:

```bash
# Aus Git entfernen (falls bereits committed)
git rm -r --cached dist/
git rm -r --cached build/

# .gitignore aktualisieren
echo "dist/" >> .gitignore
echo "build/" >> .gitignore

# Committen
git add .gitignore
git commit -m "Remove large build directories"
git push
```

## 7. README anpassen

Passen Sie die Download-Links in der README.md an:

Ersetzen Sie `USERNAME` mit Ihrem GitHub-Benutzernamen:
- `https://github.com/USERNAME/taskcard-downloader`

## Fertig!

Ihr Projekt ist jetzt auf GitHub:
- **Code**: `https://github.com/USERNAME/taskcard-downloader`
- **Releases**: `https://github.com/USERNAME/taskcard-downloader/releases`
- **Actions**: `https://github.com/USERNAME/taskcard-downloader/actions`

Die Apps werden automatisch bei jedem Push neu gebaut!
