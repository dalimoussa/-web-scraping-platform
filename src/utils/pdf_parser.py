"""
PDF parsing utilities for extracting funding data from PDF reports.
Supports both tabular extraction and OCR fallback.
"""

from typing import Dict, Optional, List, Any
from pathlib import Path
import re
import tempfile

from ..core.logger import get_logger


logger = get_logger(__name__)


def extract_tables_from_pdf(pdf_path: str) -> List[List[List[str]]]:
    """
    Extract tables from PDF using pdfplumber.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of tables (each table is list of rows)
    """
    try:
        import pdfplumber
        
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        
        logger.info(f"Extracted {len(tables)} tables from {pdf_path}")
        return tables
        
    except ImportError:
        logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")
        return []
    except Exception as e:
        logger.error(f"Failed to extract tables from {pdf_path}: {e}")
        return []


def extract_text_from_pdf_ocr(pdf_path: str) -> str:
    """
    Extract text from PDF using OCR (for scanned PDFs).
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        text = ""
        for i, image in enumerate(images):
            logger.debug(f"OCR processing page {i+1}/{len(images)}")
            page_text = pytesseract.image_to_string(image, lang='jpn+eng')
            text += page_text + "\n"
        
        logger.info(f"Extracted {len(text)} characters via OCR from {pdf_path}")
        return text
        
    except ImportError as e:
        logger.warning(f"OCR dependencies not installed: {e}")
        logger.warning("Install with: pip install pdf2image pytesseract")
        logger.warning("Also install Tesseract-OCR: brew install tesseract (macOS) or from GitHub")
        return ""
    except Exception as e:
        logger.error(f"OCR extraction failed for {pdf_path}: {e}")
        return ""


def parse_funding_totals_from_text(text: str) -> Dict[str, Optional[float]]:
    """
    Parse funding totals from extracted text.
    
    Args:
        text: Extracted text from PDF
        
    Returns:
        Dict with income_total, expense_total, balance
    """
    totals = {
        'income_total': None,
        'expense_total': None,
        'balance': None,
    }
    
    # Japanese patterns
    patterns = [
        # Income patterns
        (r'収入[合計総額\s]*[:：]\s*([0-9,]+)\s*円?', 'income_total'),
        (r'収入総額[：:]\s*([0-9,]+)', 'income_total'),
        (r'総収入[：:]\s*([0-9,]+)', 'income_total'),
        
        # Expense patterns
        (r'支出[合計総額\s]*[:：]\s*([0-9,]+)\s*円?', 'expense_total'),
        (r'支出総額[：:]\s*([0-9,]+)', 'expense_total'),
        (r'総支出[：:]\s*([0-9,]+)', 'expense_total'),
        
        # Balance patterns
        (r'残高[：:]\s*([0-9,]+)', 'balance'),
        (r'差引[残高]*[：:]\s*([0-9,]+)', 'balance'),
    ]
    
    for pattern, key in patterns:
        if totals[key] is None:  # Only set if not already found
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    totals[key] = float(amount_str)
                    logger.debug(f"Found {key}: {totals[key]}")
                except ValueError:
                    pass
    
    # Calculate balance if not found
    if totals['balance'] is None and totals['income_total'] and totals['expense_total']:
        totals['balance'] = totals['income_total'] - totals['expense_total']
    
    return totals


def parse_funding_from_tables(tables: List[List[List[str]]]) -> Dict[str, Optional[float]]:
    """
    Parse funding totals from extracted tables.
    
    Args:
        tables: List of tables from PDF
        
    Returns:
        Dict with income_total, expense_total, balance
    """
    totals = {
        'income_total': None,
        'expense_total': None,
        'balance': None,
    }
    
    # Keywords to identify rows
    income_keywords = ['収入', '総収入', 'income']
    expense_keywords = ['支出', '総支出', 'expense']
    balance_keywords = ['残高', '差引', 'balance']
    
    for table in tables:
        for row in table:
            if not row or len(row) < 2:
                continue
            
            # Convert row to strings
            row_strs = [str(cell).lower() if cell else '' for cell in row]
            row_text = ' '.join(row_strs)
            
            # Look for amounts (numbers with commas)
            amounts = []
            for cell in row:
                if cell:
                    cleaned = str(cell).replace(',', '').replace('円', '').strip()
                    if cleaned.replace('.', '').isdigit():
                        try:
                            amounts.append(float(cleaned))
                        except ValueError:
                            pass
            
            if not amounts:
                continue
            
            # Match keywords to amounts
            if any(kw in row_text for kw in income_keywords) and not totals['income_total']:
                totals['income_total'] = max(amounts)  # Usually the largest number
                
            elif any(kw in row_text for kw in expense_keywords) and not totals['expense_total']:
                totals['expense_total'] = max(amounts)
                
            elif any(kw in row_text for kw in balance_keywords) and not totals['balance']:
                totals['balance'] = amounts[0]
    
    return totals


def download_and_parse_pdf(
    pdf_url: str,
    http_client,
    use_ocr: bool = False,
) -> Dict[str, Any]:
    """
    Download PDF and extract funding data.
    
    Args:
        pdf_url: URL to PDF
        http_client: HTTP client for downloading
        use_ocr: Whether to use OCR if table extraction fails
        
    Returns:
        Dict with totals and extracted text
    """
    result = {
        'income_total': None,
        'expense_total': None,
        'balance': None,
        'text_preview': None,
    }
    
    try:
        # Download PDF
        logger.info(f"Downloading PDF: {pdf_url}")
        response = http_client.get_safe(pdf_url)
        
        if not response:
            logger.warning(f"Failed to download PDF: {pdf_url}")
            return result
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            # Try table extraction first
            tables = extract_tables_from_pdf(tmp_path)
            if tables:
                totals = parse_funding_from_tables(tables)
                result.update(totals)
            
            # If no totals found and OCR enabled, try OCR
            if use_ocr and not any([result['income_total'], result['expense_total']]):
                logger.info("Table extraction incomplete, trying OCR...")
                text = extract_text_from_pdf_ocr(tmp_path)
                if text:
                    totals = parse_funding_totals_from_text(text)
                    result.update(totals)
                    result['text_preview'] = text[:500]  # First 500 chars
        
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    except Exception as e:
        logger.error(f"Failed to parse PDF {pdf_url}: {e}")
    
    return result
