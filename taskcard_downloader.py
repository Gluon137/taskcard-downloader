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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import argparse
import json
import requests
import aiohttp
import asyncio
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

    async def download_and_save(self, include_pdf_attachments=True):
        """
        Orchestrates the download process:
        1. Launches browser
        2. Extracts data
        3. Downloads attachments (via browser)
        4. Downloads images (via aiohttp parallel)
        5. Generates PDF
        Returns list of downloaded files for JSON export.
        """
        print(f"Start Taskcard download process for: {self.url}")
        
        # Prepare output directory
        output_path = Path(self.output_file)
        attachments_dir = output_path.parent / f"{output_path.stem}_attachments"
        if include_pdf_attachments:
            attachments_dir.mkdir(exist_ok=True)
            
        downloaded_files = [] 
        
        async with async_playwright() as p:
            # Launch browser once
            browser = await p.chromium.launch(headless=True)
            # Create context with accept_downloads=True from the start
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                # 1. Load and Extract Data
                await self._load_and_extract_data(page)
                
                # 2. Download Attachments (files that need clicking)
                if include_pdf_attachments:
                    att_files = await self._download_clickable_attachments(page, attachments_dir)
                    downloaded_files.extend(att_files)
                    
            finally:
                await browser.close()
        
        # 3. Download Images (Parallel) - outside of browser context as we just need URLs
        if include_pdf_attachments and self.data.get('columns'):
            image_files = await self._download_images_parallel(attachments_dir)
            downloaded_files.extend(image_files)
            
        # 4. Generate PDF
        self.generate_pdf(downloaded_files)
        
        return downloaded_files

    async def _load_and_extract_data(self, page):
        """Loads page and extracts data using the provided page object"""
        print(f"Öffne Taskcard: {self.url}")
        
        # Navigate to the page
        await page.goto(self.url, wait_until='networkidle', timeout=30000)

        # Wait for content to load
        print("Warte auf Seiteninhalt...")
        await page.wait_for_timeout(5000)

        # Scroll logic to trigger lazy loading
        await self._scroll_page(page)

        # Save screenshot
        debug_screenshot = Path(self.output_file).parent / 'taskcard_debug.png'
        try:
             await page.screenshot(path=str(debug_screenshot), full_page=True)
             print(f"Screenshot gespeichert: {debug_screenshot}")
        except Exception as e:
            print(f"Screenshot Fehler: {e}")

        # Extract data implementation
        await self._extract_data_js(page, debug_screenshot)
        
    async def _scroll_page(self, page):
        """Handles the scrolling logic"""
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

            # Scroll in steps
            current_scroll = 0
            step = 600
            while current_scroll < scroll_width:
                await page.evaluate(f'''
                    () => {{
                        const container = document.querySelector('.board-container');
                        if (container) {{
                            container.scrollLeft = {current_scroll};
                        }}
                    }}
                ''')
                await page.wait_for_timeout(500)
                current_scroll += step

            # Scroll to end and back
            await page.evaluate('''
                () => {
                    const container = document.querySelector('.board-container');
                    if (container) container.scrollLeft = container.scrollWidth;
                }
            ''')
            await page.wait_for_timeout(1000)
            
            await page.evaluate('''
                () => {
                    const container = document.querySelector('.board-container');
                    if (container) container.scrollLeft = 0;
                }
            ''')
            await page.wait_for_timeout(1000)
            
    async def _extract_data_js(self, page, debug_screenshot):
        """Runs the JS extraction logic"""
        # (This contains the large JS block from the original code)
        debug_info = await page.evaluate("""
            () => {
                const columns = document.querySelectorAll('.draggableList');
                return columns.length;
            }
        """)
        print(f"DEBUG: Gefundene Spalten-Container: {debug_info}")

        # Extract data using JavaScript
        data = await page.evaluate("""
            () => {
                const result = {
                    board_title: '',
                    columns: [],
                    extraction_strategy: '',
                    debug_info: ''
                };

                // Extract board title with fallbacks
                const titleContainer = document.querySelector('.board-information-title');
                if (titleContainer) {
                    result.board_title = titleContainer.innerText.trim();
                } else {
                    const headerTitle = document.querySelector('h1, .board-header-container .text-h5');
                    if (headerTitle) {
                        result.board_title = headerTitle.innerText.trim();
                    } else {
                        result.board_title = document.title || 'Unbenanntes Board';
                    }
                }

                // Helper function to extract card data
                const extractCardData = (cardEl) => {
                    const card = {
                        title: '',
                        description: '',
                        links: [],
                        attachments: [],
                        images: []
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
                            if (!card.links.find(l => l.url === href)) {
                                card.links.push({ text, url: href });
                            }
                        }

                        // Get images from card - normal <img> tags
                        const images = cardContent.querySelectorAll('img');
                        for (const img of images) {
                            const src = img.src;
                            const alt = img.alt || 'Bild';
                            if (src && src.startsWith('http')) {
                                card.images.push({ src, alt });
                            }
                        }

                        // Get background images (Taskcard Preview Style)
                        const bgImages = cardContent.querySelectorAll('.q-img__image');
                        for (const div of bgImages) {
                            const bgStyle = div.style.backgroundImage;
                            if (bgStyle) {
                                const urlMatch = bgStyle.match(/url\\("?(.+?)"?\\)/);
                                if (urlMatch) {
                                    card.images.push({
                                        src: urlMatch[1],
                                        alt: 'Hintergrundbild'
                                    });
                                }
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

                    return card;
                };

                // STRATEGY 1: Column Layout (Kanban)
                const columns = document.querySelectorAll('.draggableList');

                if (columns.length > 0) {
                    result.extraction_strategy = 'Spalten-Layout (Kanban)';
                    result.debug_info = `${columns.length} Spalte(n) erkannt`;

                    for (const col of columns) {
                        const columnData = {
                            title: '',
                            cards: []
                        };

                        const colHeaderDiv = col.querySelector('.board-list-header .contenteditable');
                        if (colHeaderDiv) {
                            columnData.title = colHeaderDiv.innerText.trim();
                        }

                        const cardElements = col.querySelectorAll('.board-card');
                        for (const cardEl of cardElements) {
                            const card = extractCardData(cardEl);
                            if (card.title || card.description || card.links.length > 0 || card.attachments.length > 0 || card.images.length > 0) {
                                columnData.cards.push(card);
                            }
                        }

                        if (columnData.title || columnData.cards.length > 0) {
                            result.columns.push(columnData);
                        }
                    }

                // STRATEGY 2: Free Layout (Pinboard/Timeline)
                } else {
                    const allCards = document.querySelectorAll('.board-card');

                    if (allCards.length > 0) {
                        result.extraction_strategy = 'Freies Layout (Pinnwand/Tafel)';
                        result.debug_info = `${allCards.length} Karte(n) ohne Spalten gefunden`;

                        const fallbackColumn = {
                            title: 'Alle Inhalte (Freies Layout)',
                            cards: []
                        };

                        for (const cardEl of allCards) {
                            const card = extractCardData(cardEl);
                            if (card.title || card.description || card.links.length > 0 || card.attachments.length > 0 || card.images.length > 0) {
                                fallbackColumn.cards.push(card);
                            }
                        }
                        result.columns.push(fallbackColumn);
                    } else {
                         result.extraction_strategy = 'FEHLER: Keine Inhalte erkannt';
                    }
                }
                return result;
            }
        """)

        self.data = data
        self._print_extraction_summary(debug_screenshot)

    def _print_extraction_summary(self, debug_screenshot):
        """Prints summary of extracted data"""
        strategy = self.data.get('extraction_strategy', 'Unbekannt')
        debug_info = self.data.get('debug_info', '')

        print(f"\n{'='*60}")
        print(f"📋 EXTRAKTIONS-STRATEGIE: {strategy}")
        print(f"ℹ️  {debug_info}")
        print(f"{'='*60}")

        print(f"\nBoard-Titel: {self.data['board_title']}")
        print(f"Gefundene Spalten: {len(self.data['columns'])}")

        for idx, col in enumerate(self.data['columns']):
            total_images = sum(len(card.get('images', [])) for card in col['cards'])
            print(f"  Spalte {idx+1}: {col['title']} ({len(col['cards'])} Karten, {total_images} Bilder)")

        if self.data.get('extraction_strategy', '').startswith('FEHLER'):
            print("\n⚠️  WARNUNG: Keine Inhalte gefunden!")
            print(f"    Debug-Screenshot: {debug_screenshot}")

    async def _download_clickable_attachments(self, page, attachments_dir):
        """Downloads file attachments by clicking them in the browser"""
        print("\nLade klickbare Anhänge über Browser herunter...")
        downloaded_files = [] 
        
        # Find clickable attachments
        border_attachments = await page.query_selector_all('[class*="border cursor-pointer"]')
        qitem_attachments = await page.query_selector_all('.q-item--clickable:has(i[class*="mdi-file"])')
        file_links = await page.query_selector_all('.board-card-content a[href*="download"]')
        
        all_attachments = list(border_attachments) + list(qitem_attachments) + list(file_links)
        print(f"  Gefunden: {len(all_attachments)} potentielle Anhänge")

        for idx, att_div in enumerate(all_attachments):
            try:
                caption_text = None
                # Try finding text
                qitem_label = await att_div.query_selector('.q-item__label')
                if qitem_label:
                    caption_text = await qitem_label.inner_text()
                else:
                    caption = await att_div.query_selector('.text-caption')
                    if caption:
                        caption_text = await caption.inner_text()
                
                if not caption_text:
                    caption_text = f"Anhang {idx+1}"

                print(f"  [{idx+1}/{len(all_attachments)}] Lade: {caption_text[:60]}...")

                try:
                    async with page.expect_download(timeout=10000) as download_info:
                        await att_div.click()
                    
                    download = await download_info.value
                    suggested_filename = download.suggested_filename
                    safe_filename = "".join(c for c in suggested_filename if c.isalnum() or c in (' ', '.', '_', '-')).strip() or f"attachment_{idx}.bin"
                    
                    final_path = attachments_dir / safe_filename
                    counter = 1
                    while final_path.exists():
                        name, ext = os.path.splitext(safe_filename)
                        final_path = attachments_dir / f"{name}_{counter}{ext}"
                        counter += 1
                        
                    await download.save_as(str(final_path))
                    
                    downloaded_files.append({
                        'info': caption_text,
                        'file_path': str(final_path),
                        'type': 'file'
                    })
                    print(f"      ✓ Gespeichert: {final_path.name}")
                    
                except Exception as down_err:
                    print(f"      ⚠️  Kein Download ausgelöst oder Timeout (kein File?): {str(down_err)[:50]}")
                    
            except Exception as e:
                print(f"      ⚠️  Fehler bei Anhang {idx}: {e}")
                
        return downloaded_files

    async def _download_images_parallel(self, attachments_dir):
        """Downloads all images in parallel using aiohttp"""
        all_images = []
        for col in self.data.get('columns', []):
            for card in col.get('cards', []):
                for image in card.get('images', []):
                    if image.get('src'):
                        all_images.append(image)
        
        if not all_images:
            return []
            
        print(f"\nLade {len(all_images)} Bilder parallel herunter...")
        
        downloaded_images = []
        semaphore = asyncio.Semaphore(10)  # Limit concurrency
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for idx, img in enumerate(all_images):
                tasks.append(self._download_single_image(session, img, attachments_dir, idx, semaphore))
                
            results = await asyncio.gather(*tasks)
            
            # Filter None results
            for res in results:
                if res:
                    downloaded_images.append(res)
                    
        print(f"  {len(downloaded_images)}/{len(all_images)} Bilder erfolgreich geladen.")
        return downloaded_images

    async def _download_single_image(self, session, image_data, attachments_dir, idx, semaphore):
        """Helper to download a single image"""
        src = image_data.get('src')
        alt = image_data.get('alt', 'Bild')
        
        async with semaphore:
            try:
                async with session.get(src, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Guess extension
                        content_type = response.headers.get('content-type', '')
                        if 'png' in content_type: ext = '.png'
                        elif 'jpeg' in content_type or 'jpg' in content_type: ext = '.jpg'
                        elif 'gif' in content_type: ext = '.gif'
                        elif 'webp' in content_type: ext = '.webp'
                        else: ext = '.jpg'
                        
                        # Filename
                        safe_name = "".join(c for c in alt if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                        if not safe_name: safe_name = f"image_{idx}"
                        
                        # Save
                        final_path = attachments_dir / f"{safe_name}{ext}"
                        counter = 1
                        while final_path.exists():
                            final_path = attachments_dir / f"{safe_name}_{counter}{ext}"
                            counter += 1
                            
                        with open(final_path, 'wb') as f:
                            f.write(content)
                            
                        # Update local path in data
                        image_data['local_path'] = str(final_path)
                        
                        print(f"  ✓ Bild geladen: {final_path.name}")
                        return {
                            'info': f"Bild: {alt}",
                            'file_path': str(final_path),
                            'type': 'image'
                        }
            except Exception as e:
                print(f"  ⚠️  Fehler bei Bild {alt[:20]}: {e}")
                return None

    # Keeping old method name for compatibility if needed, but it should be unused
    async def fetch_taskcard_data(self): 


        return await self.download_and_save()
    



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

        # Add extraction strategy info
        strategy = self.data.get('extraction_strategy', '')
        if strategy:
            strategy_style = ParagraphStyle('StrategyStyle', parent=styles['Normal'],
                fontSize=9, textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER, fontName='Helvetica-Oblique')
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(f"Extrahiert mit: {self._escape_html(strategy)}", strategy_style))

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

                    # Card images
                    images = card.get('images', [])
                    if images:
                        for img in images:
                            local_path = img.get('local_path')
                            alt = img.get('alt', 'Bild')

                            if local_path and os.path.exists(local_path):
                                try:
                                    # Calculate maximum width (PDF page width minus margins)
                                    max_width = A4[0] - 4*cm  # 2cm left + 2cm right margin
                                    max_height = 10*cm  # Maximum height to prevent huge images

                                    # Create ReportLab Image object
                                    img_obj = RLImage(local_path)

                                    # Get original dimensions
                                    img_width = img_obj.imageWidth
                                    img_height = img_obj.imageHeight

                                    # Calculate scaling to fit within max dimensions
                                    width_scale = max_width / img_width
                                    height_scale = max_height / img_height
                                    scale = min(width_scale, height_scale, 1.0)  # Don't upscale

                                    # Set final dimensions
                                    img_obj.drawWidth = img_width * scale
                                    img_obj.drawHeight = img_height * scale

                                    # Add image to story with alt text caption
                                    story.append(Spacer(1, 0.2*cm))
                                    story.append(img_obj)

                                    # Add caption if alt text exists
                                    if alt and alt != 'Bild':
                                        caption_style = ParagraphStyle('ImageCaption', parent=card_content_style,
                                            fontSize=9, textColor=colors.HexColor('#666666'),
                                            fontName='Helvetica-Oblique', alignment=TA_CENTER)
                                        story.append(Spacer(1, 0.1*cm))
                                        story.append(Paragraph(self._escape_html(alt), caption_style))

                                    story.append(Spacer(1, 0.3*cm))

                                except Exception as e:
                                    print(f"Fehler beim Einfügen von Bild {local_path}: {e}")
                                    # Add note about missing image
                                    error_style = ParagraphStyle('ImageError', parent=card_content_style,
                                        fontSize=9, textColor=colors.HexColor('#ea4335'),
                                        fontName='Helvetica-Oblique')
                                    story.append(Paragraph(f"⚠️ Bild konnte nicht eingefügt werden: {alt}", error_style))
                                    story.append(Spacer(1, 0.2*cm))

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




    def export_json(self, json_file=None, downloaded_pdfs=None):
        """Export Taskcard data as JSON

        Args:
            json_file: Path to output JSON file
            downloaded_pdfs: List of downloaded PDF file paths (optional)
        """
        if json_file is None:
            json_file = self.output_file.replace('.pdf', '.json')

        # Create a mapping of PDF captions to local file paths
        pdf_mapping = {}
        if downloaded_pdfs:
            for pdf_item in downloaded_pdfs:
                # downloaded_pdfs is a list of dicts: {'info': caption, 'file_path': path}
                if isinstance(pdf_item, dict):
                    info = pdf_item.get('info', '')
                    file_path = pdf_item.get('file_path', '')
                    if info and file_path:
                        pdf_mapping[info] = file_path

        # Prepare data for export
        export_data = {
            'board_title': self.data.get('board_title', ''),
            'export_date': datetime.now().isoformat(),
            'source_url': self.url,
            'extraction_strategy': self.data.get('extraction_strategy', 'Unbekannt'),
            'debug_info': self.data.get('debug_info', ''),
            'columns': []
        }

        # Add all columns and cards
        for column in self.data.get('columns', []):
            column_data = {
                'title': column.get('title', ''),
                'cards': []
            }

            for card in column.get('cards', []):
                card_data = {
                    'title': card.get('title', ''),
                    'description': card.get('description', ''),
                    'attachments': [],
                    'links': []
                }

                # Add attachments with local file paths if available
                for attachment in card.get('attachments', []):
                    caption = attachment.get('caption', '')

                    # Try to find matching downloaded PDF by caption
                    local_file = pdf_mapping.get(caption, None)

                    # If not found by exact match, try fuzzy matching
                    if not local_file:
                        for pdf_info, pdf_path in pdf_mapping.items():
                            # Check if caption is contained in PDF info or vice versa
                            if caption and pdf_info and (caption in pdf_info or pdf_info in caption):
                                local_file = pdf_path
                                break

                    attachment_data = {
                        'caption': caption,
                        'local_file': local_file,  # Path to downloaded PDF (null if not downloaded)
                    }

                    # Add appropriate note based on whether file was downloaded
                    if local_file:
                        attachment_data['note'] = 'Datei wurde heruntergeladen - nutze local_file für Zugriff'
                    else:
                        attachment_data['note'] = 'Datei wurde nicht heruntergeladen (PDF-Anhänge Option war deaktiviert oder Download fehlgeschlagen)'

                    card_data['attachments'].append(attachment_data)

                # Add links
                for link in card.get('links', []):
                    card_data['links'].append({
                        'text': link.get('text', ''),
                        'url': link.get('url', '')
                    })

                column_data['cards'].append(card_data)

            export_data['columns'].append(column_data)

        # Write JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON erfolgreich exportiert: {json_file}")


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
