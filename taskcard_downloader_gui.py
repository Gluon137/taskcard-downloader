#!/usr/bin/env python3
"""
Taskcard Downloader GUI - Graphical interface for Taskcard downloader
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import asyncio
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

# Import the main downloader class and browser check
from taskcard_downloader import TaskcardDownloader, check_playwright_browsers, BROWSERS_PATH


class BrowserInstallerDialog:
    """Dialog for installing Playwright browsers"""

    def __init__(self, parent):
        self.parent = parent
        self.success = False

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Browser-Installation erforderlich")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300)
        y = (self.dialog.winfo_screenheight() // 2) - (200)
        self.dialog.geometry(f'600x400+{x}+{y}')

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icon and title
        title_label = ttk.Label(
            main_frame,
            text="⚠️  Browser-Installation erforderlich",
            font=('Helvetica', 14, 'bold')
        )
        title_label.pack(pady=(0, 10))

        # Message
        message = (
            "Die Taskcard Downloader App benötigt einen Browser (Chromium),\n"
            "um Taskcard-Webseiten zu laden.\n\n"
            "Die Browser-Dateien (~140 MB) werden heruntergeladen und\n"
            f"in folgendem Ordner gespeichert:\n\n{BROWSERS_PATH}\n\n"
            "Dies ist nur einmal notwendig."
        )
        message_label = ttk.Label(main_frame, text=message, justify=tk.LEFT)
        message_label.pack(pady=10)

        # Progress area
        self.progress_var = tk.StringVar(value="Bereit zur Installation")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.pack(pady=(20, 5))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=5)

        # Log output
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=8,
            width=70,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Courier', 9)
        )
        self.log_text.pack(pady=10, fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))

        self.install_button = ttk.Button(
            button_frame,
            text="Browser jetzt installieren",
            command=self.start_installation
        )
        self.install_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self.cancel
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.dialog.update()

    def start_installation(self):
        """Start browser installation in background thread"""
        self.install_button.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.progress_var.set("Installation läuft...")

        install_thread = threading.Thread(target=self.run_installation, daemon=True)
        install_thread.start()

    def run_installation(self):
        """Run the actual installation"""
        try:
            self.log("Starte Browser-Installation...")
            self.log(f"Zielordner: {BROWSERS_PATH}")
            self.log("")

            # Set environment variable
            env = os.environ.copy()
            env['PLAYWRIGHT_BROWSERS_PATH'] = str(BROWSERS_PATH)

            # Run playwright install
            process = subprocess.Popen(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Read output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(line)

            process.wait()

            if process.returncode == 0:
                self.dialog.after(0, self.installation_success)
            else:
                self.dialog.after(0, self.installation_failed, "Installation fehlgeschlagen")

        except Exception as e:
            self.dialog.after(0, self.installation_failed, str(e))

    def installation_success(self):
        """Handle successful installation"""
        self.progress_bar.stop()
        self.progress_var.set("Installation erfolgreich!")
        self.log("")
        self.log("✅ Browser erfolgreich installiert!")

        self.success = True
        self.install_button.config(state=tk.DISABLED)
        self.cancel_button.config(text="Schließen")

        messagebox.showinfo(
            "Installation erfolgreich",
            "Die Browser wurden erfolgreich installiert!\n\n"
            "Sie können jetzt die Taskcard Downloader App verwenden.",
            parent=self.dialog
        )

        self.dialog.destroy()

    def installation_failed(self, error_msg):
        """Handle installation failure"""
        self.progress_bar.stop()
        self.progress_var.set("Installation fehlgeschlagen")
        self.log("")
        self.log(f"❌ Fehler: {error_msg}")

        messagebox.showerror(
            "Installation fehlgeschlagen",
            f"Die Browser-Installation ist fehlgeschlagen:\n\n{error_msg}\n\n"
            "Die App kann ohne Browser nicht verwendet werden.",
            parent=self.dialog
        )

    def cancel(self):
        """Cancel installation"""
        if self.success:
            self.dialog.destroy()
        else:
            if messagebox.askyesno(
                "Installation abbrechen?",
                "Ohne Browser kann die App nicht verwendet werden.\n\n"
                "Möchten Sie wirklich abbrechen?",
                parent=self.dialog
            ):
                self.dialog.destroy()


class TaskcardDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Taskcard Downloader")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Variables
        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.include_attachments_var = tk.BooleanVar(value=True)
        self.export_json_var = tk.BooleanVar(value=False)
        self.is_downloading = False

        self.setup_ui()

    def _bind_entry_shortcuts(self, entry):
        """Bind keyboard shortcuts for Entry widget to fix PyInstaller/macOS issues"""
        # macOS Command key bindings
        entry.bind('<Command-a>', lambda e: entry.select_range(0, tk.END) or 'break')
        entry.bind('<Command-c>', lambda e: self.root.clipboard_clear() or self.root.clipboard_append(entry.selection_get()) or 'break')
        entry.bind('<Command-x>', lambda e: (self.root.clipboard_clear(), self.root.clipboard_append(entry.selection_get()), entry.delete(tk.SEL_FIRST, tk.SEL_LAST)) if entry.selection_present() else None)
        entry.bind('<Command-v>', lambda e: entry.insert(tk.INSERT, self.root.clipboard_get()) or 'break')

        # Also bind Control key as fallback
        entry.bind('<Control-a>', lambda e: entry.select_range(0, tk.END) or 'break')
        entry.bind('<Control-c>', lambda e: self.root.clipboard_clear() or self.root.clipboard_append(entry.selection_get()) or 'break')
        entry.bind('<Control-x>', lambda e: (self.root.clipboard_clear(), self.root.clipboard_append(entry.selection_get()), entry.delete(tk.SEL_FIRST, tk.SEL_LAST)) if entry.selection_present() else None)
        entry.bind('<Control-v>', lambda e: entry.insert(tk.INSERT, self.root.clipboard_get()) or 'break')

    def setup_ui(self):
        """Setup the user interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Taskcard Downloader",
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # URL Input
        ttk.Label(main_frame, text="Taskcard URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_entry = tk.Entry(main_frame, textvariable=self.url_var, width=50, font=('Helvetica', 11))
        url_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        url_entry.config(state='normal')  # Explicitly set to normal state
        # Enable copy-paste on macOS
        self._bind_entry_shortcuts(url_entry)
        self.url_entry = url_entry  # Store reference

        # Output file
        ttk.Label(main_frame, text="Ausgabe-Datei:").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_entry = tk.Entry(main_frame, textvariable=self.output_var, width=50, font=('Helvetica', 11))
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        output_entry.config(state='normal')  # Explicitly set to normal state
        # Enable copy-paste on macOS
        self._bind_entry_shortcuts(output_entry)
        self.output_entry = output_entry  # Store reference

        browse_button = ttk.Button(main_frame, text="Durchsuchen...", command=self.browse_output)
        browse_button.grid(row=2, column=2, sticky=tk.W, pady=5)

        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Optionen", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(0, weight=1)

        attachments_check = ttk.Checkbutton(
            options_frame,
            text="Anhänge herunterladen (PDFs werden ins Haupt-PDF integriert, andere Dateien separat gespeichert)",
            variable=self.include_attachments_var
        )
        attachments_check.grid(row=0, column=0, sticky=tk.W)

        json_export_check = ttk.Checkbutton(
            options_frame,
            text="Auch als JSON exportieren (für Weiterverarbeitung)",
            variable=self.export_json_var
        )
        json_export_check.grid(row=1, column=0, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.download_button = ttk.Button(
            button_frame,
            text="Download starten",
            command=self.start_download,
            style='Accent.TButton'
        )
        self.download_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self.cancel_download,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        clear_button = ttk.Button(
            button_frame,
            text="Felder leeren",
            command=self.clear_fields
        )
        clear_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress_var = tk.StringVar(value="Bereit")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Status-Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=70,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Courier', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Info text at bottom
        info_text = "Hinweis: Der Download kann 2-5 Minuten dauern, je nach Anzahl der PDF-Anhänge."
        info_label = ttk.Label(main_frame, text=info_text, foreground="gray", font=('Helvetica', 9))
        info_label.grid(row=8, column=0, columnspan=3, pady=5)

        # Set default output filename in Documents/TaskCards
        default_name = f"taskcard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        default_dir = Path.home() / "Documents" / "TaskCards"
        # Create directory if it doesn't exist
        default_dir.mkdir(parents=True, exist_ok=True)
        self.output_var.set(str(default_dir / default_name))

    def browse_output(self):
        """Open file dialog to select output location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=Path(self.output_var.get()).name,
            initialdir=Path(self.output_var.get()).parent
        )
        if filename:
            self.output_var.set(filename)

    def clear_fields(self):
        """Clear all input fields"""
        if not self.is_downloading:
            self.url_var.set("")
            default_name = f"taskcard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            default_dir = Path.home() / "Documents" / "TaskCards"
            default_dir.mkdir(parents=True, exist_ok=True)
            self.output_var.set(str(default_dir / default_name))
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.progress_var.set("Bereit")

    def log(self, message):
        """Add message to log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_download(self):
        """Start the download process in a separate thread"""
        # Validate inputs
        if not self.url_var.get().strip():
            messagebox.showerror("Fehler", "Bitte geben Sie eine Taskcard-URL ein.")
            return

        if not self.output_var.get().strip():
            messagebox.showerror("Fehler", "Bitte geben Sie einen Ausgabe-Dateinamen an.")
            return

        # Update UI state
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)
        self.progress_var.set("Download läuft...")

        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Start download in separate thread
        download_thread = threading.Thread(target=self.run_download, daemon=True)
        download_thread.start()

    def run_download(self):
        """Run the actual download process"""
        try:
            url = self.url_var.get().strip()
            output_file = self.output_var.get().strip()
            include_attachments = self.include_attachments_var.get()
            export_json = self.export_json_var.get()

            self.log(f"Starte Download...")
            self.log(f"URL: {url}")
            self.log(f"Ausgabe: {output_file}")
            self.log(f"PDF-Anhänge: {'Ja' if include_attachments else 'Nein'}")
            self.log(f"JSON-Export: {'Ja' if export_json else 'Nein'}")
            self.log("-" * 70)

            # Create downloader with temporary name
            downloader = TaskcardDownloader(url, output_file)

            # Redirect output to log
            import io
            import contextlib
            import re

            log_capture = io.StringIO()

            # Run async download
            async def download_task():
                # First fetch the data to get the board title
                await downloader.fetch_taskcard_data()

                # Update output filename based on board title
                if downloader.data.get('board_title'):
                    # Sanitize the board title for use as filename
                    board_title = downloader.data['board_title']
                    # Remove invalid filename characters
                    safe_title = re.sub(r'[<>:"/\\|?*]', '', board_title)
                    # Limit length to 100 characters
                    safe_title = safe_title[:100].strip()

                    # Update the output file with the board title
                    output_path = Path(output_file)
                    new_filename = f"{safe_title}.pdf"
                    new_output_file = output_path.parent / new_filename
                    downloader.output_file = str(new_output_file)

                    # Update the GUI output field
                    self.root.after(0, self.output_var.set, str(new_output_file))
                    self.root.after(0, self.log, f"Dateiname angepasst: {new_filename}")

                # Now save the PDF and get downloaded PDFs list
                downloaded_pdfs = await downloader.download_and_save(include_pdf_attachments=include_attachments)

                # Export JSON if requested
                if export_json:
                    json_file = Path(downloader.output_file).with_suffix('.json')
                    downloader.export_json(str(json_file), downloaded_pdfs=downloaded_pdfs)
                    self.root.after(0, self.log, f"✅ JSON erfolgreich exportiert: {json_file}")

            # Capture output
            with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
                asyncio.run(download_task())

            # Get captured output and display it
            output = log_capture.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self.log(line)

            # Use the actual output file (may have been renamed)
            final_output = downloader.output_file
            self.root.after(0, self.download_complete_success, final_output)

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self.download_complete_error, error_msg)

    def download_complete_success(self, output_file):
        """Handle successful download completion"""
        self.progress_bar.stop()
        self.progress_var.set("Download abgeschlossen!")
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

        self.log("-" * 70)
        self.log("✅ DOWNLOAD ERFOLGREICH ABGESCHLOSSEN!")
        self.log(f"Datei gespeichert: {output_file}")

        # Show success message with option to open file
        result = messagebox.askyesno(
            "Download abgeschlossen",
            f"Die Taskcard wurde erfolgreich heruntergeladen!\n\n"
            f"Datei: {Path(output_file).name}\n\n"
            f"Möchten Sie die Datei öffnen?"
        )

        if result:
            import subprocess
            import platform

            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', output_file])
                elif platform.system() == 'Windows':
                    subprocess.run(['start', output_file], shell=True)
                else:  # Linux
                    subprocess.run(['xdg-open', output_file])
            except Exception as e:
                messagebox.showerror("Fehler", f"Konnte Datei nicht öffnen: {e}")

    def download_complete_error(self, error_msg):
        """Handle download error"""
        self.progress_bar.stop()
        self.progress_var.set("Fehler beim Download")
        self.is_downloading = False
        self.download_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

        self.log("-" * 70)
        self.log(f"❌ FEHLER: {error_msg}")

        messagebox.showerror(
            "Download fehlgeschlagen",
            f"Beim Download ist ein Fehler aufgetreten:\n\n{error_msg}\n\n"
            f"Bitte prüfen Sie die URL und Ihre Internetverbindung."
        )

    def cancel_download(self):
        """Cancel the download (placeholder - actual cancellation is complex)"""
        if messagebox.askyesno("Abbrechen", "Möchten Sie den Download wirklich abbrechen?"):
            self.log("\n⚠️  Abbruch durch Benutzer...")
            # Note: Proper cancellation would require more complex implementation
            self.progress_bar.stop()
            self.progress_var.set("Abgebrochen")
            self.is_downloading = False
            self.download_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)


def main():
    """Main entry point for GUI"""
    root = tk.Tk()

    # Set style
    style = ttk.Style()
    style.theme_use('default')

    # Check if browsers are installed (should always be true with bundled browser)
    if not check_playwright_browsers():
        messagebox.showerror(
            "Browser fehlt",
            "Die erforderlichen Browser-Dateien wurden nicht gefunden.\n\n"
            "Die App kann nicht verwendet werden."
        )
        root.destroy()
        return

    # Create and run app
    app = TaskcardDownloaderGUI(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == '__main__':
    main()
