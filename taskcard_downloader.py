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

                # Save screenshot for debugging (full width)
                await page.screenshot(path='taskcard_debug.png', full_page=True)
                print("Screenshot gespeichert: taskcard_debug.png")

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
                            const cardElements = col.querySelectorAll('.draggableCard');

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

                # Find all PDF attachment divs
                attachment_divs = await page.query_selector_all('[class*="border cursor-pointer"]')
                print(f"  Gefunden: {len(attachment_divs)} Anhänge")

                for idx, att_div in enumerate(attachment_divs):
                    try:
                        # Get attachment info
                        caption = await att_div.query_selector('.text-caption')
                        if caption:
                            caption_text = await caption.inner_text()

                            # Only process PDFs
                            if 'PDF' in caption_text.upper():
                                print(f"  [{idx+1}/{len(attachment_divs)}] Lade: {caption_text[:60]}...")

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
        """Generates PDF from collected data and merges with downloaded PDFs"""
        print(f"\nGeneriere Übersichts-PDF...")

        # Create PDF document
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Container for PDF elements
        story = []

        # Define styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        column_style = ParagraphStyle(
            'ColumnTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34a853'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        )

        card_title_style = ParagraphStyle(
            'CardTitle',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#ea4335'),
            spaceAfter=6,
            spaceBefore=10,
            leftIndent=20,
            fontName='Helvetica-Bold'
        )

        card_content_style = ParagraphStyle(
            'CardContent',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=30,
            spaceAfter=4,
            fontName='Helvetica'
        )

        link_style = ParagraphStyle(
            'Link',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1a73e8'),
            leftIndent=35,
            spaceAfter=3,
            fontName='Helvetica'
        )

        # Add board title
        if self.data['board_title']:
            story.append(Paragraph(self._escape_html(self.data['board_title']), title_style))
        else:
            story.append(Paragraph("Taskcard Board", title_style))

        story.append(Spacer(1, 0.3*cm))

        # Add date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(Spacer(1, 0.8*cm))

        # Add columns and cards
        for col_idx, column in enumerate(self.data['columns']):
            # Column title
            if column['title']:
                story.append(Paragraph(f"▶ {self._escape_html(column['title'])}", column_style))
            else:
                story.append(Paragraph(f"▶ Spalte {col_idx + 1}", column_style))

            if not column['cards']:
                no_cards_style = ParagraphStyle(
                    'NoCards',
                    parent=card_content_style,
                    fontName='Helvetica-Oblique'
                )
                story.append(Paragraph("<i>Keine Karten vorhanden</i>", no_cards_style))
            else:
                for card_idx, card in enumerate(column['cards']):
                    # Card title
                    if card['title']:
                        story.append(Paragraph(f"● {self._escape_html(card['title'])}", card_title_style))
                    else:
                        story.append(Paragraph(f"● Karte {card_idx + 1}", card_title_style))

                    # Card description
                    if card['description'] and card['description'].strip():
                        # Split long descriptions into paragraphs
                        desc_lines = card['description'].split('\n')
                        for line in desc_lines:
                            if line.strip():
                                story.append(Paragraph(self._escape_html(line.strip()), card_content_style))

                    # Card attachments
                    if card.get('attachments'):
                        attachment_style = ParagraphStyle(
                            'Attachment',
                            parent=styles['Normal'],
                            fontSize=9,
                            textColor=colors.HexColor('#666666'),
                            leftIndent=35,
                            spaceAfter=3,
                            fontName='Helvetica'
                        )
                        for att in card['attachments']:
                            # Handle both old format (string) and new format (dict)
                            if isinstance(att, dict):
                                att_text = f"📎 {self._escape_html(att.get('info', ''))}"
                            else:
                                att_text = f"📎 {self._escape_html(att)}"
                            story.append(Paragraph(att_text, attachment_style))

                    # Card links
                    if card['links']:
                        for link in card['links']:
                            link_text = f"🔗 <a href='{link['url']}' color='blue'>{self._escape_html(link['text'][:80])}</a>"
                            if len(link['text']) > 80:
                                link_text += "..."
                            story.append(Paragraph(link_text, link_style))

                    story.append(Spacer(1, 0.2*cm))

            story.append(Spacer(1, 0.4*cm))

        # Build PDF
        try:
            # Create overview PDF
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
            doc.build(story)

            print(f"  Übersicht erstellt")
            print(f"   Spalten: {len(self.data['columns'])}")
            total_cards = sum(len(col['cards']) for col in self.data['columns'])
            print(f"   Karten gesamt: {total_cards}")

            # Merge with downloaded PDFs if available
            if downloaded_pdfs and len(downloaded_pdfs) > 0:
                print(f"\nFüge {len(downloaded_pdfs)} PDF-Anhänge zusammen...")
                self._merge_pdfs(temp_overview.name, downloaded_pdfs)
            else:
                # No PDFs to merge, just copy the overview
                import shutil
                shutil.copy(temp_overview.name, self.output_file)

            # Clean up temp file
            os.unlink(temp_overview.name)

            print(f"✅ PDF erfolgreich erstellt: {self.output_file}")

        except Exception as e:
            print(f"❌ Fehler beim Erstellen des PDFs: {e}")
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
