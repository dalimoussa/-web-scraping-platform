"""
Funding scraper - extracts political funding/activity fund reports.
Sources: SOUMU political funds disclosure, prefectural portals.
"""

from typing import List, Dict, Any, Optional
import re

from .base import BaseScraper
from ..utils.parsers import (
    parse_html,
    extract_text,
    extract_links,
    clean_text,
    normalize_url,
)
from ..core.config import load_sources


class FundingScraper(BaseScraper):
    """Scraper for political funding reports."""
    
    def __init__(self, *args, **kwargs):
        """Initialize funding scraper."""
        super().__init__(*args, **kwargs)
        self.sources = load_sources()
        self.parse_totals = self.config.get('targets.funding.parse_totals', False)
    
    def scrape(
        self,
        urls: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape funding reports.
        
        Args:
            urls: List of URLs to scrape (uses config if None)
            limit: Maximum number to scrape
            
        Returns:
            List of funding records
        """
        self.clear_results()
        
        if urls is None:
            urls = self._get_funding_source_urls()
        
        if not urls:
            self.logger.warning("No funding source URLs configured")
            return []
        
        self.logger.info(f"Scraping {len(urls)} funding sources")
        
        if limit:
            urls = urls[:limit]
        
        for idx, url in enumerate(urls, 1):
            try:
                self.logger.info(f"Scraping {idx}/{len(urls)}: {url}")
                funding_records = self._scrape_funding_page(url)
                
                for record in funding_records:
                    self.add_result(record)
                
                self.log_progress(idx, len(urls), "sources")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Found {len(self.results)} funding records")
        return self.get_results()
    
    def _get_funding_source_urls(self) -> List[str]:
        """Get funding source URLs from config."""
        urls = []
        
        funding_sources = self.sources.get('funding_sources', {})
        
        # National sources
        for source in funding_sources.get('national', []):
            if isinstance(source, dict):
                urls.append(source.get('url'))
            elif isinstance(source, str):
                urls.append(source)
        
        # Prefectural sources
        for source in funding_sources.get('prefectural', []):
            if isinstance(source, dict):
                urls.append(source.get('url'))
            elif isinstance(source, str):
                urls.append(source)
        
        return [u for u in urls if u]
    
    def _scrape_funding_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape single page for funding data.
        
        Args:
            url: Page URL
            
        Returns:
            List of funding records
        """
        records = []
        
        try:
            response = self.http.get(url)
            if not response:
                return records
            
            soup = parse_html(response.text)
            
            # Strategy 1: Find PDF/report links
            report_links = self._find_report_links(soup, url)
            
            for link in report_links:
                # Extract metadata from link text and context
                link_info = self._parse_report_link(link, url)
                
                if link_info:
                    record = {
                        'official_id': None,  # TODO: Match with officials
                        'year': link_info.get('year'),
                        'report_url': link_info.get('url'),
                        'income_total': None,
                        'expense_total': None,
                        'balance': None,
                        'currency': 'JPY',
                        'source_url': url,
                        'last_updated': self.get_timestamp(),
                    }
                    
                    # Optionally parse totals if enabled
                    if self.parse_totals and link_info.get('url'):
                        totals = self._parse_report_totals(link_info['url'])
                        record.update(totals)
                    
                    records.append(record)
            
            # Strategy 2: Parse tables with funding data
            tables = soup.find_all('table')
            for table in tables:
                table_records = self._parse_funding_table(table, url)
                records.extend(table_records)
            
        except Exception as e:
            self.logger.error(f"Error parsing funding from {url}: {e}")
        
        return records
    
    def _find_report_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """
        Find links to funding reports (PDFs, pages, etc.).
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relatives
            
        Returns:
            List of link dicts with url and text
        """
        links = []
        
        # Keywords that indicate funding reports
        keywords = [
            '収支報告', '政治資金', '資金報告', '収支',
            'funding', 'report', 'finance', 'disclosure'
        ]
        
        for a_tag in soup.find_all('a', href=True):
            link_text = extract_text(a_tag).lower()
            href = a_tag['href']
            
            # Check if link text contains keywords
            if any(kw in link_text for kw in keywords):
                full_url = normalize_url(href, base_url)
                
                links.append({
                    'url': full_url,
                    'text': extract_text(a_tag),
                    'element': a_tag,
                })
        
        return links
    
    def _parse_report_link(self, link: Dict[str, str], source_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse metadata from report link.
        
        Args:
            link: Link dict with url and text
            source_url: Source page URL
            
        Returns:
            Dict with parsed info or None
        """
        text = link.get('text', '')
        url = link.get('url', '')
        
        # Extract year from link text or URL
        year = self._extract_year(text) or self._extract_year(url)
        
        if not year:
            # Default to current year if not found
            from datetime import datetime
            year = datetime.now().year
        
        return {
            'url': url,
            'year': year,
            'text': text,
        }
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text."""
        # Pattern for Japanese year (令和X年 -> Reiwa X)
        reiwa_match = re.search(r'令和(\d+)年', text)
        if reiwa_match:
            reiwa_year = int(reiwa_match.group(1))
            return 2018 + reiwa_year  # Reiwa 1 = 2019
        
        # Pattern for Western year
        year_match = re.search(r'(20\d{2})', text)
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _parse_report_totals(self, url: str) -> Dict[str, Optional[float]]:
        """
        Parse income/expense totals from report page.
        
        Args:
            url: Report URL
            
        Returns:
            Dict with income_total, expense_total, balance
        """
        totals = {
            'income_total': None,
            'expense_total': None,
            'balance': None,
        }
        
        try:
            # Only parse HTML pages, skip PDFs
            if url.lower().endswith('.pdf'):
                self.logger.debug(f"Skipping PDF parsing: {url}")
                return totals
            
            response = self.http.get_safe(url)
            if not response:
                return totals
            
            soup = parse_html(response.text)
            page_text = soup.get_text()
            
            # Look for total amounts
            # Pattern: 収入合計：12,345,678円
            income_match = re.search(r'収入[合計総額：\s]+([0-9,]+)', page_text)
            if income_match:
                amount_str = income_match.group(1).replace(',', '')
                totals['income_total'] = float(amount_str)
            
            expense_match = re.search(r'支出[合計総額：\s]+([0-9,]+)', page_text)
            if expense_match:
                amount_str = expense_match.group(1).replace(',', '')
                totals['expense_total'] = float(amount_str)
            
            # Calculate balance if both available
            if totals['income_total'] is not None and totals['expense_total'] is not None:
                totals['balance'] = totals['income_total'] - totals['expense_total']
            
        except Exception as e:
            self.logger.warning(f"Failed to parse totals from {url}: {e}")
        
        return totals
    
    def _parse_funding_table(self, table, source_url: str) -> List[Dict[str, Any]]:
        """
        Parse funding data from table.
        
        Args:
            table: BeautifulSoup table element
            source_url: Source page URL
            
        Returns:
            List of funding records
        """
        records = []
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return records
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            cell_texts = [extract_text(cell) for cell in cells]
            
            # Try to extract year and amounts
            year = None
            income = None
            expense = None
            
            for text in cell_texts:
                # Look for year
                if not year:
                    year = self._extract_year(text)
                
                # Look for amounts (numbers with commas)
                amount_str = text.replace(',', '').replace('円', '').strip()
                if amount_str.isdigit():
                    amount = float(amount_str)
                    if income is None:
                        income = amount
                    elif expense is None:
                        expense = amount
            
            if year or income or expense:
                record = {
                    'official_id': None,
                    'year': year,
                    'report_url': source_url,
                    'income_total': income,
                    'expense_total': expense,
                    'balance': (income - expense) if (income and expense) else None,
                    'currency': 'JPY',
                    'source_url': source_url,
                    'last_updated': self.get_timestamp(),
                }
                records.append(record)
        
        return records
