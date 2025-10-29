"""
Google Sheets Integration Module
Extracts municipal website URLs from Google Spreadsheet Column H.
Supports both public CSV export and Google Sheets API.
"""

import re
import csv
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

import requests
from ..core.http_client import HTTPClient
from ..core.config import Config


class GoogleSheetsReader:
    """Read municipal URLs from Google Sheets."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize Google Sheets reader."""
        self.config = config or Config()
        self.http = HTTPClient()  # Use default settings
        self.logger = logging.getLogger(__name__)
    
    def extract_urls_from_spreadsheet(
        self,
        spreadsheet_url: str,
        column: str = "H",
        sheet_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract URLs from Google Spreadsheet column.
        
        Args:
            spreadsheet_url: Google Sheets URL
            column: Column letter to extract (default: H)
            sheet_name: Specific sheet name (optional)
            
        Returns:
            List of dicts with municipality info and URLs
        """
        self.logger.info(f"Extracting URLs from spreadsheet: {spreadsheet_url}")
        
        # Try CSV export first (fastest, works for public sheets)
        try:
            return self._extract_from_csv_export(spreadsheet_url, column, sheet_name)
        except Exception as e:
            self.logger.warning(f"CSV export failed: {e}")
        
        # Fallback: Parse HTML (works if sheet is viewable)
        try:
            return self._extract_from_html(spreadsheet_url, column, sheet_name)
        except Exception as e:
            self.logger.error(f"HTML parsing failed: {e}")
        
        # If all methods fail, return empty list
        self.logger.error("All extraction methods failed")
        return []
    
    def _extract_from_csv_export(
        self,
        spreadsheet_url: str,
        column: str,
        sheet_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract URLs using CSV export feature."""
        # Convert Sheets URL to CSV export URL
        csv_url = self._convert_to_csv_url(spreadsheet_url, sheet_name)
        
        self.logger.info(f"Downloading CSV from: {csv_url}")
        response = self.http.get(csv_url)
        
        if not response or response.status_code != 200:
            raise ValueError(f"Failed to download CSV: {response.status_code if response else 'No response'}")
        
        # Parse CSV content - use content.decode to ensure proper UTF-8 decoding
        # Google Sheets exports CSV in UTF-8 with BOM
        csv_content = response.content.decode('utf-8-sig')
        return self._parse_csv_content(csv_content, column)
    
    def _convert_to_csv_url(
        self,
        spreadsheet_url: str,
        sheet_name: Optional[str] = None,
    ) -> str:
        """Convert Google Sheets URL to CSV export URL."""
        # Extract spreadsheet ID from URL
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', spreadsheet_url)
        if not match:
            raise ValueError(f"Invalid Google Sheets URL: {spreadsheet_url}")
        
        spreadsheet_id = match.group(1)
        
        # Extract gid (sheet ID) if present
        gid_match = re.search(r'[#&]gid=([0-9]+)', spreadsheet_url)
        gid = gid_match.group(1) if gid_match else '0'
        
        # Build CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        
        return csv_url
    
    def _parse_csv_content(
        self,
        csv_content: str,
        column: str,
    ) -> List[Dict[str, Any]]:
        """Parse CSV content and extract data from specified column."""
        results = []
        
        # Convert column letter to index (A=0, B=1, ..., H=7)
        column_index = ord(column.upper()) - ord('A')
        
        # Parse CSV
        lines = csv_content.strip().split('\n')
        reader = csv.reader(lines)
        
        # Process rows
        headers = None
        for row_num, row in enumerate(reader, 1):
            # Skip empty rows at start
            if row_num < 100:  # Data starts around row 100 in this sheet
                continue
            
            # Skip rows with only commas
            if not any(cell.strip() for cell in row):
                continue
            
            # First row might be headers
            if row_num == 1:
                headers = row
                # Check if first row looks like headers (not URLs)
                if column_index < len(row) and not self._is_url(row[column_index]):
                    continue
            
            # Extract data from columns
            if len(row) > 1:  # Need at least 2 columns
                prefecture = row[0].strip() if len(row) > 0 else ''
                city_name = row[1].strip() if len(row) > 1 else ''
                
                # Skip empty rows
                if not prefecture and not city_name:
                    continue
                
                municipality_data = {
                    'row_number': row_num,
                    'prefecture': prefecture,
                    'municipality_name': city_name,
                    'url': None,  # Will be generated
                    'raw_row': row,
                }
                
                # Check if column has a URL
                if column_index < len(row):
                    cell_value = row[column_index].strip()
                    if self._is_url(cell_value):
                        municipality_data['url'] = cell_value
                
                results.append(municipality_data)
        
        self.logger.info(f"Extracted {len(results)} municipalities from CSV")
        return results
    
    def _extract_from_html(
        self,
        spreadsheet_url: str,
        column: str,
        sheet_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract URLs by parsing HTML (fallback method)."""
        # This is a fallback for when CSV export doesn't work
        # Implementation would parse the HTML view of the sheet
        # For now, raise NotImplementedError
        raise NotImplementedError("HTML parsing not yet implemented. Use CSV export or make sheet public.")
    
    def _is_url(self, text: str) -> bool:
        """Check if text is a valid URL."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        return bool(url_pattern.match(text))
    
    def _extract_municipality_name(
        self,
        row: List[str],
        headers: Optional[List[str]],
    ) -> Optional[str]:
        """Extract municipality name from row (heuristic)."""
        # Common column names for municipality
        name_keywords = ['市区町村', '自治体', '名称', 'municipality', 'name', '市', '区', '町', '村']
        
        if headers:
            for idx, header in enumerate(headers):
                if any(keyword in header.lower() for keyword in name_keywords):
                    if idx < len(row):
                        return row[idx].strip()
        
        # Fallback: try first column if it looks like a name
        if row and row[0] and not self._is_url(row[0]):
            return row[0].strip()
        
        return None
    
    def _extract_prefecture(
        self,
        row: List[str],
        headers: Optional[List[str]],
    ) -> Optional[str]:
        """Extract prefecture name from row (heuristic)."""
        # Common column names for prefecture
        prefecture_keywords = ['都道府県', 'prefecture', '県', '都', '府', '道']
        
        if headers:
            for idx, header in enumerate(headers):
                if any(keyword in header.lower() for keyword in prefecture_keywords):
                    if idx < len(row):
                        return row[idx].strip()
        
        return None
    
    def save_urls_to_file(
        self,
        urls: List[Dict[str, Any]],
        output_path: Path,
    ) -> None:
        """Save extracted URLs to CSV file for later use."""
        self.logger.info(f"Saving {len(urls)} URLs to {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            if urls:
                fieldnames = ['row_number', 'municipality_name', 'prefecture', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in urls:
                    writer.writerow({
                        'row_number': item.get('row_number', ''),
                        'municipality_name': item.get('municipality_name', ''),
                        'prefecture': item.get('prefecture', ''),
                        'url': item.get('url', ''),
                    })
        
        self.logger.info(f"Saved URLs to {output_path}")
    
    def load_urls_from_file(
        self,
        input_path: Path,
    ) -> List[Dict[str, Any]]:
        """Load previously extracted URLs from CSV file."""
        self.logger.info(f"Loading URLs from {input_path}")
        
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        urls = []
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row)
        
        self.logger.info(f"Loaded {len(urls)} URLs from {input_path}")
        return urls


# Convenience function
def extract_municipal_urls(
    spreadsheet_url: str,
    column: str = "H",
    output_file: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Extract municipal URLs from Google Spreadsheet.
    
    Args:
        spreadsheet_url: Google Sheets URL
        column: Column letter to extract (default: H)
        output_file: Optional path to save URLs
        
    Returns:
        List of municipality data with URLs
        
    Example:
        >>> urls = extract_municipal_urls(
        ...     "https://docs.google.com/spreadsheets/d/1Jaxeb_GVozSC2kU38LTExrI-PXl_o0dB0HqwkIZsGP0/edit",
        ...     column="H"
        ... )
        >>> print(f"Found {len(urls)} municipalities")
    """
    reader = GoogleSheetsReader()
    urls = reader.extract_urls_from_spreadsheet(spreadsheet_url, column)
    
    if output_file:
        reader.save_urls_to_file(urls, output_file)
    
    return urls
