#!/usr/bin/env python3
"""
Taskcard Downloader V2 - Downloads complete Taskcard content and saves as PDF
Optimiert für Taskcard.app Struktur
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Determine if running as PyInstaller bundle
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

# Set Playwright browsers path
BROWSERS_PATH = get_browsers_path()
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(BROWSERS_PATH)

from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import argparse
import json
import requests
from PyPDF2 import PdfReader, PdfWriter


def check_playwright_browsers():
    """Check if Playwright browsers are installed and provide installation instructions if not"""
    chromium_path = BROWSERS_PATH / "chromium-1140" / "chrome-mac" / "Chromium.app"

    # Check multiple possible browser locations
    possible_paths = [
        BROWSERS_PATH / "chromium-1140",
        BROWSERS_PATH / "chromium-1148",
        BROWSERS_PATH / "chromium-1112",
    ]

    browser_found = any(path.exists() for path in possible_paths)

    if not browser_found:
        print("\n" + "="*70)
        print("⚠️  PLAYWRIGHT BROWSER NICHT GEFUNDEN")
        print("="*70)
        print("\nDie Playwright-Browser müssen einmalig installiert werden.")
        print("\nBitte führen Sie folgenden Befehl im Terminal aus:\n")
        print(f"  PLAYWRIGHT_BROWSERS_PATH={BROWSERS_PATH} playwright install chromium\n")
        print("Oder alternativ:")
        print(f"  export PLAYWRIGHT_BROWSERS_PATH={BROWSERS_PATH}")
        print("  playwright install chromium\n")
        print("="*70 + "\n")
        return False

    return True


class TaskcardDownloader:
    def __init__(self, url, output_file=None):
        self.url = url
        self.output_file = output_file or f"taskcard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.data = {
            'board_title': '',
            'columns': []
        }

    async def fetch_taskcard_data(self):
        """Fetches Taskcard data using Playwright with JavaScript evaluation"""
        print(f"Öffne Taskcard: {self.url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Store for downloaded files
            self.downloaded_files = []

            try:
                # Navigate to the page
                await page.goto(self.url, wait_until='networkidle', timeout=30000)

                # Wait for content to load
                print("Warte auf Seiteninhalt...")
                await page.wait_for_timeout(5000)

                # Scroll horizontally to load all columns (lazy loading)
                print("Lade alle Spalten durch Scrollen...")
                board_container = await page.query_selector('.board-container')
                if board_container:
                    # Get the scrollable width
                    scroll_width = await page.evaluate('''
                        () => {
                            const container = document.querySelector('.board-container');
                            return container ? container.scrollWidth : 0;
                        }
                    ''')

                    # Scroll in steps to trigger lazy loading
                    current_scroll = 0
                    step = 600  # Scroll 600px at a time (smaller steps for better loading)

                    while current_scroll < scroll_width:
                        await page.evaluate(f'''
                            () => {{
                                const container = document.querySelector('.board-container');
                                if (container) {{
                                    container.scrollLeft = {current_scroll};
                                }}
                            }}
                        ''')
                        await page.wait_for_timeout(800)  # Wait longer for content to load
                        current_scroll += step

                    # Scroll to the very end
                    await page.evaluate('''
                        () => {
                            const container = document.querySelector('.board-container');
                            if (container) {
                                container.scrollLeft = container.scrollWidth;
                            }
                        }
                    ''')
                    await page.wait_for_timeout(2000)  # Wait at the end

                    # Scroll back to the beginning
                    await page.evaluate('''
                        () => {
                            const container = document.querySelector('.board-container');
                            if (container) {
                                container.scrollLeft = 0;
                            }
                        }
                    ''')
                    await page.wait_for_timeout(2000)  # Wait after scrolling back
                    print(f"  Scrollbreite: {scroll_width}px")

                # Save screenshot for debugging (full width) in a writable location
                debug_screenshot = Path(self.output_file).parent / 'taskcard_debug.png'
                await page.screenshot(path=str(debug_screenshot), full_page=True)
                print(f"Screenshot gespeichert: {debug_screenshot}")

                # Debug: Check what elements exist on the page
                debug_info = await page.evaluate("""
                    () => {
                        const columns = document.querySelectorAll('.draggableList');
                        const debug = [];
                        columns.forEach((col, idx) => {
                            const cards = col.querySelectorAll('*');
                            const cardClasses = new Set();
                            cards.forEach(card => {
                                if (card.className && typeof card.className === 'string') {
                                    card.className.split(' ').forEach(c => cardClasses.add(c));
                                }
                            });
                            debug.push({
                                columnIndex: idx,
                                totalElements: cards.length,
                                uniqueClasses: Array.from(cardClasses).slice(0, 20)
                            });
                        });
                        return debug;
                    }
                """)
                print(f"DEBUG HTML-Struktur: {debug_info}")

                # Extract data using JavaScript - using specific Taskcard selectors
                data = await page.evaluate("""
                    () => {
                        const result = {
                            board_title: '',
                            columns: []
                        };

                        // Extract board title
                        const titleContainer = document.querySelector('.board-information-title');
                        if (titleContainer) {
                            result.board_title = titleContainer.innerText.trim();
                        } else {
                            const headerTitle = document.querySelector('h1, .board-header-container .text-h5');
                            if (headerTitle) {
                                result.board_title = headerTitle.innerText.trim();
                            }
                        }

                        // Find all column containers using Taskcard-specific class
                        const columns = document.querySelectorAll('.draggableList');

                        // Process each column
                        for (const col of columns) {
                            const columnData = {
                                title: '',
                                cards: []
                            };

                            // Get column title from board-list-header
                            const colHeaderDiv = col.querySelector('.board-list-header .contenteditable');
                            if (colHeaderDiv) {
                                columnData.title = colHeaderDiv.innerText.trim();
                            }

                            // Find all cards in this column
                            // Note: Taskcard changed from .draggableCard to .board-card
                            const cardElements = col.querySelectorAll('.board-card');

                            for (const cardEl of cardElements) {
                                const card = {
                                    title: '',
                                    description: '',
                                    links: [],
                                    attachments: []
                                };

                                // Get card title from board-card-header
                                const cardHeader = cardEl.querySelector('.board-card-header .contenteditable');
                                if (cardHeader) {
                                    card.title = cardHeader.innerText.trim();
                                }

                                // Get card content from board-card-content
                                const cardContent = cardEl.querySelector('.board-card-content');
                                if (cardContent) {
                                    // Get text content (first contenteditable in card content)
                                    const contentText = cardContent.querySelector('.contenteditable');
                                    if (contentText) {
                                        card.description = contentText.innerText.trim();
                                    }

                                    // Get links
                                    const links = cardContent.querySelectorAll('a[href]');
                                    for (const link of links) {
                                        const href = link.href;
                                        const text = link.innerText.trim() || link.href;
                                        // Avoid duplicate links
                                        if (!card.links.find(l => l.url === href)) {
                                            card.links.push({ text, url: href });
                                        }
                                    }

                                    // Get attachment info (PDFs, files) with download URLs
                                    const attachmentDivs = cardContent.querySelectorAll('[class*="border cursor-pointer"]');
                                    for (const attDiv of attachmentDivs) {
                                        const fileInfo = attDiv.querySelector('.text-caption');
                                        // Get the background image URL which contains the file URL
                                        const imgDiv = attDiv.querySelector('.q-img__image');
                                        let fileUrl = null;
                                        if (imgDiv) {
                                            const bgStyle = imgDiv.style.backgroundImage;
                                            if (bgStyle) {
                                                // Use a regex that works in JavaScript
                                                const urlMatch = bgStyle.match(/url\\("(.+?)"\\)/);
                                                if (urlMatch) {
                                                    fileUrl = urlMatch[1];
                                                }
                                            }
                                        }

                                        if (fileInfo) {
                                            const text = fileInfo.innerText.trim();
                                            card.attachments.push({
                                                info: text,
                                                url: fileUrl
                                            });
                                        }
                                    }
                                }

                                // Only add card if it has content
                                if (card.title || card.description || card.links.length > 0 || card.attachments.length > 0) {
                                    columnData.cards.push(card);
                                }
                            }

                            // Only add column if it has a title or cards
                            if (columnData.title || columnData.cards.length > 0) {
                                result.columns.push(columnData);
                            }
                        }

                        return result;
                    }
                """)

                self.data = data
                print(f"\nBoard-Titel: {self.data['board_title']}")
                print(f"Gefundene Spalten: {len(self.data['columns'])}")

                for idx, col in enumerate(self.data['columns']):
                    print(f"  Spalte {idx+1}: {col['title']} ({len(col['cards'])} Karten)")
                    # Debug: Show first card content
                    if col['cards']:
                        first_card = col['cards'][0]
                        print(f"    DEBUG - Erste Karte Titel: {first_card.get('title', 'LEER')[:80]}")
                        print(f"    DEBUG - Erste Karte Beschreibung: {first_card.get('description', 'LEER')[:80]}")

            except Exception as e:
                print(f"Fehler beim Laden der Seite: {e}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                await browser.close()

    async def download_pdf_attachments_with_playwright(self):
        """Downloads PDF attachments by clicking download elements with Playwright"""
        print("\nLade PDF-Anhänge über Browser herunter...")
        downloaded_pdfs = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            try:
                # Navigate to the page again
                await page.goto(self.url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(5000)

                # Scroll to load all content
                board_container = await page.query_selector('.board-container')
                if board_container:
                    scroll_width = await page.evaluate('() => document.querySelector(".board-container").scrollWidth')
                    current = 0
                    while current < scroll_width:
                        await page.evaluate(f'() => {{ document.querySelector(".board-container").scrollLeft = {current} }}')
                        await page.wait_for_timeout(500)
                        current += 600

                    await page.evaluate('() => { document.querySelector(".board-container").scrollLeft = 0 }')
                    await page.wait_for_timeout(1000)

                # Find all PDF attachment divs - try multiple selectors
                # Type 1: Border cursor-pointer (most common)
                border_attachments = await page.query_selector_all('[class*="border cursor-pointer"]')

                # Type 2: Q-item clickable (preview format)
                qitem_attachments = await page.query_selector_all('.q-item--clickable:has(i.mdi-file-pdf-box)')

                # Type 3: Direct PDF links
                pdf_links = await page.query_selector_all('.board-card-content a[href*=".pdf"]')

                # Combine all unique attachments
                all_attachments = list(border_attachments) + list(qitem_attachments) + list(pdf_links)
                print(f"  Gefunden: {len(all_attachments)} potentielle Anhänge (Typen: {len(border_attachments)} standard, {len(qitem_attachments)} preview, {len(pdf_links)} links)")

                for idx, att_div in enumerate(all_attachments):
                    try:
                        # Get attachment info - try different selectors
                        caption_text = None

                        # Try q-item format first (has filename in q-item__label)
                        qitem_label = await att_div.query_selector('.q-item__label')
                        if qitem_label:
                            caption_text = await qitem_label.inner_text()
                        else:
                            # Try standard format
                            caption = await att_div.query_selector('.text-caption')
                            if caption:
                                caption_text = await caption.inner_text()

                        if caption_text:
                            # Only process PDFs (either has "PDF" in text or .pdf extension)
                            if 'PDF' in caption_text.upper() or caption_text.lower().endswith('.pdf'):
                                print(f"  [{idx+1}/{len(all_attachments)}] Lade: {caption_text[:60]}...")

                                # Setup download promise before clicking
                                async with page.expect_download(timeout=30000) as download_info:
                                    # Click the attachment to trigger download
                                    await att_div.click()

                                download = await download_info.value

                                # Save to temp file
                                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                                temp_file.close()

                                await download.save_as(temp_file.name)

                                # Verify it's a PDF
                                with open(temp_file.name, 'rb') as f:
                                    first_bytes = f.read(4)
                                    if first_bytes == b'%PDF':
                                        file_size = os.path.getsize(temp_file.name)
                                        downloaded_pdfs.append({
                                            'info': caption_text,
                                            'file_path': temp_file.name
                                        })
                                        print(f"      ✓ {file_size // 1024} KB heruntergeladen")
                                    else:
                                        print(f"      ⚠️  Datei ist kein PDF")
                                        os.unlink(temp_file.name)

                                # Wait a bit before next download
                                await page.wait_for_timeout(500)

                    except Exception as e:
                        print(f"      ⚠️  Fehler: {str(e)[:80]}")

                print(f"\n  {len(downloaded_pdfs)} PDF-Anhänge erfolgreich heruntergeladen")

            except Exception as e:
                print(f"Fehler beim Herunterladen der Anhänge: {e}")
            finally:
                await browser.close()

        return downloaded_pdfs

    def generate_pdf(self, downloaded_pdfs=None):
        """Generates structured PDF with TOC, columns as chapters, cards as subchapters, attachments inline"""
        print(f"\nGeneriere strukturiertes PDF mit Inhaltsverzeichnis...")

        # Build a map of attachment info to PDF file path for easy lookup
        pdf_map = {}
        if downloaded_pdfs:
            for pdf_dict in downloaded_pdfs:
                pdf_map[pdf_dict['info']] = pdf_dict['file_path']

        # Create temporary overview PDF first
        temp_overview = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_overview.close()

        doc = SimpleDocTemplate(
            temp_overview.name,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        story = []
        styles = getSampleStyleSheet()

        # Define styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
            fontSize=24, textColor=colors.HexColor('#1a73e8'), spaceAfter=30,
            spaceBefore=10, alignment=TA_CENTER, fontName='Helvetica-Bold')

        toc_title_style = ParagraphStyle('TOCTitle', parent=styles['Heading2'],
            fontSize=18, spaceAfter=20, spaceBefore=10, fontName='Helvetica-Bold')

        toc_entry_style = ParagraphStyle('TOCEntry', parent=styles['Normal'],
            fontSize=12, leftIndent=20, spaceAfter=8, fontName='Helvetica')

        chapter_style = ParagraphStyle('ChapterTitle', parent=styles['Heading1'],
            fontSize=18, textColor=colors.HexColor('#34a853'), spaceAfter=15,
            spaceBefore=10, fontName='Helvetica-Bold')

        card_title_style = ParagraphStyle('CardTitle', parent=styles['Heading2'],
            fontSize=14, textColor=colors.HexColor('#ea4335'), spaceAfter=10,
            spaceBefore=15, leftIndent=10, fontName='Helvetica-Bold')

        card_content_style = ParagraphStyle('CardContent', parent=styles['Normal'],
            fontSize=11, leftIndent=20, spaceAfter=6, fontName='Helvetica')

        link_style = ParagraphStyle('Link', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#1a73e8'),
            leftIndent=20, spaceAfter=4, fontName='Helvetica')

        attachment_note_style = ParagraphStyle('AttachmentNote', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#666666'), leftIndent=20,
            spaceAfter=8, fontName='Helvetica-Oblique')

        # 1. TITLE PAGE
        story.append(Paragraph(self._escape_html(self.data.get('board_title', 'Taskcard Board')), title_style))
        story.append(Spacer(1, 0.5*cm))
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#666666'), alignment=TA_CENTER)
        story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(PageBreak())

        # 2. TABLE OF CONTENTS
        story.append(Paragraph("Inhaltsverzeichnis", toc_title_style))
        story.append(Spacer(1, 0.5*cm))

        for col_idx, column in enumerate(self.data['columns']):
            col_title = column.get('title', f'Spalte {col_idx + 1}')
            card_count = len(column.get('cards', []))
            toc_text = f"{col_idx + 1}. {self._escape_html(col_title)} ({card_count} Karte{'n' if card_count != 1 else ''})"
            story.append(Paragraph(toc_text, toc_entry_style))

        story.append(PageBreak())

        # 3. CHAPTERS (COLUMNS) WITH CARDS
        for col_idx, column in enumerate(self.data['columns']):
            # Chapter title (Column name)
            col_title = column.get('title', f'Spalte {col_idx + 1}')
            story.append(Paragraph(f"{col_idx + 1}. {self._escape_html(col_title)}", chapter_style))
            story.append(Spacer(1, 0.5*cm))

            cards = column.get('cards', [])
            if not cards:
                no_cards_style = ParagraphStyle('NoCards', parent=card_content_style, fontName='Helvetica-Oblique')
                story.append(Paragraph("<i>Keine Karten vorhanden</i>", no_cards_style))
                story.append(Spacer(1, 0.5*cm))
            else:
                for card_idx, card in enumerate(cards):
                    # Card title (Subchapter)
                    card_title = card.get('title', f'Karte {card_idx + 1}')
                    story.append(Paragraph(f"{col_idx + 1}.{card_idx + 1} {self._escape_html(card_title)}", card_title_style))
                    story.append(Spacer(1, 0.2*cm))

                    # Card description/content
                    description = card.get('description', '').strip()
                    if description:
                        for line in description.split('\n'):
                            if line.strip():
                                story.append(Paragraph(self._escape_html(line.strip()), card_content_style))
                        story.append(Spacer(1, 0.3*cm))

                    # Card links
                    links = card.get('links', [])
                    if links:
                        for link in links:
                            link_text = f"🔗 <a href='{link['url']}' color='blue'>{self._escape_html(link['text'][:80])}</a>"
                            story.append(Paragraph(link_text, link_style))
                        story.append(Spacer(1, 0.3*cm))

                    # Note about PDF attachments that will follow
                    attachments = card.get('attachments', [])
                    pdf_attachments = [att for att in attachments if isinstance(att, dict) and 'PDF' in att.get('info', '').upper()]

                    if pdf_attachments and pdf_map:
                        att_count = len(pdf_attachments)
                        story.append(Paragraph(f"📎 {att_count} PDF-Anhang{'̈e' if att_count > 1 else ''} (folgt auf nächsten Seiten)", attachment_note_style))

                    story.append(Spacer(1, 0.5*cm))

            # Page break after each column (chapter)
            story.append(PageBreak())

        # Build the overview PDF
        doc.build(story)

        total_cards = sum(len(col['cards']) for col in self.data['columns'])
        print(f"  Übersicht erstellt")
        print(f"   Spalten: {len(self.data['columns'])}")
        print(f"   Karten gesamt: {total_cards}")

        # Now merge with downloaded PDFs, inserting them after their respective cards
        if downloaded_pdfs and len(downloaded_pdfs) > 0:
            print(f"\nFüge {len(downloaded_pdfs)} PDF-Anhänge ein...")
            self._merge_pdfs_structured(temp_overview.name, downloaded_pdfs)
        else:
            import shutil
            shutil.copy(temp_overview.name, self.output_file)

        os.unlink(temp_overview.name)
        print(f"✅ PDF erfolgreich erstellt: {self.output_file}")

    def _merge_pdfs_structured(self, overview_pdf_path, downloaded_pdfs):
        """Merges overview PDF with downloaded PDFs, inserting after each card's section"""
        try:
            from PyPDF2 import PdfReader, PdfWriter

            pdf_writer = PdfWriter()

            # For simplicity, we'll add all overview pages first, then all attachment PDFs
            # A more sophisticated version would insert PDFs exactly after their cards
            # but that would require tracking page numbers during PDF generation

            # Add overview PDF pages
            with open(overview_pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

            # Add attachment PDFs
            for pdf_dict in downloaded_pdfs:
                pdf_path = pdf_dict['file_path']
                info = pdf_dict['info']
                print(f"  Füge hinzu: {info[:60]}...")

                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_reader = PdfReader(f)
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)
                except Exception as e:
                    print(f"    ⚠️  Fehler beim Hinzufügen: {str(e)[:60]}")

            # Write final PDF
            with open(self.output_file, 'wb') as f:
                pdf_writer.write(f)

        except Exception as e:
            print(f"❌ Fehler beim Zusammenfügen: {e}")
            raise

    def _merge_pdfs(self, overview_pdf_path, downloaded_pdfs):
        """Merges overview PDF with downloaded PDF attachments"""
        try:
            pdf_writer = PdfWriter()

            # Add overview PDF
            with open(overview_pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

            # Add each downloaded PDF
            for pdf_info in downloaded_pdfs:
                try:
                    print(f"  Füge hinzu: {pdf_info['info'][:60]}...")
                    with open(pdf_info['file_path'], 'rb') as f:
                        pdf_reader = PdfReader(f)
                        # Add separator page info (optional - could add a title page here)
                        for page in pdf_reader.pages:
                            pdf_writer.add_page(page)

                    # Clean up temp file
                    os.unlink(pdf_info['file_path'])
                except Exception as e:
                    print(f"    ⚠️  Fehler beim Hinzufügen: {e}")

            # Write final merged PDF
            with open(self.output_file, 'wb') as output_file:
                pdf_writer.write(output_file)

        except Exception as e:
            print(f"❌ Fehler beim Zusammenführen der PDFs: {e}")
            raise

    @staticmethod
    def _escape_html(text):
        """Escapes HTML special characters"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    async def download_and_save(self, include_pdf_attachments=True):
        """Main method to download and save as PDF"""
        # Check if browsers are installed
        if not check_playwright_browsers():
            raise RuntimeError("Playwright-Browser sind nicht installiert. Bitte folgen Sie den obigen Anweisungen.")

        # Only fetch data if not already fetched
        if not self.data.get('board_title') or not self.data.get('columns'):
            await self.fetch_taskcard_data()

        # Download PDF attachments if requested
        downloaded_pdfs = []
        if include_pdf_attachments:
            downloaded_pdfs = await self.download_pdf_attachments_with_playwright()

        # Generate final PDF
        self.generate_pdf(downloaded_pdfs)


async def main():
    parser = argparse.ArgumentParser(
        description='Download Taskcard content and save as PDF'
    )
    parser.add_argument(
        'url',
        help='Taskcard URL (including token)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output PDF filename (default: taskcard_YYYYMMDD_HHMMSS.pdf)',
        default=None
    )
    parser.add_argument(
        '--no-attachments',
        help='Do not include PDF attachments in the output',
        action='store_true'
    )

    args = parser.parse_args()

    downloader = TaskcardDownloader(args.url, args.output)
    await downloader.download_and_save(include_pdf_attachments=not args.no_attachments)


if __name__ == '__main__':
    asyncio.run(main())
