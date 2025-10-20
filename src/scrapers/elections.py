"""
Elections scraper - extracts election schedules and results.
Sources: SOUMU election committees, prefectural sites.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseScraper
from ..utils.parsers import (
    parse_html,
    extract_text,
    extract_links,
    extract_date_from_text,
    clean_text,
    normalize_url,
)
from ..core.config import load_sources


class ElectionsScraper(BaseScraper):
    """Scraper for election schedules and results."""
    
    def __init__(self, *args, **kwargs):
        """Initialize elections scraper."""
        super().__init__(*args, **kwargs)
        self.sources = load_sources()
        self.election_results: List[Dict[str, Any]] = []
    
    def scrape_schedules(
        self,
        urls: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape scheduled elections.
        
        Args:
            urls: List of URLs to scrape (uses config if None)
            limit: Maximum number to scrape
            
        Returns:
            List of election records
        """
        self.clear_results()
        
        if urls is None:
            urls = self._get_election_source_urls()
        
        if not urls:
            self.logger.warning("No election source URLs configured")
            return []
        
        self.logger.info(f"Scraping {len(urls)} election sources for schedules")
        
        if limit:
            urls = urls[:limit]
        
        for idx, url in enumerate(urls, 1):
            try:
                self.logger.info(f"Scraping {idx}/{len(urls)}: {url}")
                elections = self._scrape_election_schedule_page(url)
                
                for election in elections:
                    self.add_result(election)
                
                self.log_progress(idx, len(urls), "sources")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Found {len(self.results)} scheduled elections")
        return self.get_results()
    
    def scrape_results(
        self,
        urls: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape election results.
        
        Args:
            urls: List of result URLs (uses config if None)
            limit: Maximum number to scrape
            
        Returns:
            List of election result records
        """
        self.election_results = []
        
        if urls is None:
            urls = self._get_election_source_urls()
        
        if not urls:
            self.logger.warning("No election result URLs configured")
            return []
        
        self.logger.info(f"Scraping {len(urls)} sources for results")
        
        if limit:
            urls = urls[:limit]
        
        for idx, url in enumerate(urls, 1):
            try:
                self.logger.info(f"Scraping results {idx}/{len(urls)}: {url}")
                results = self._scrape_election_results_page(url)
                
                self.election_results.extend(results)
                self.log_progress(idx, len(urls), "sources")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape results {url}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Found {len(self.election_results)} election results")
        return self.election_results
    
    def _get_election_source_urls(self) -> List[str]:
        """Get election source URLs from config."""
        urls = []
        
        election_sources = self.sources.get('election_sources', {})
        
        # National sources
        for source in election_sources.get('national', []):
            if isinstance(source, dict):
                urls.append(source.get('url'))
            elif isinstance(source, str):
                urls.append(source)
        
        # Prefectural sources
        for source in election_sources.get('prefectural', []):
            if isinstance(source, dict):
                urls.append(source.get('url'))
            elif isinstance(source, str):
                urls.append(source)
        
        return [u for u in urls if u]
    
    def _scrape_election_schedule_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape single page for election schedules.
        
        Args:
            url: Page URL
            
        Returns:
            List of election records
        """
        elections = []
        
        try:
            response = self.http.get(url)
            if not response:
                return elections
            
            soup = parse_html(response.text)
            
            # Strategy 1: Look for tables with election data
            tables = soup.find_all('table')
            for table in tables:
                elections.extend(self._parse_election_table(table, url))
            
            # Strategy 2: Look for list items
            if not elections:
                lists = soup.find_all(['ul', 'ol'])
                for lst in lists:
                    elections.extend(self._parse_election_list(lst, url))
            
            # Strategy 3: Generic content extraction
            if not elections:
                # Look for date patterns in text
                page_text = soup.get_text()
                dates = self._extract_all_dates(page_text)
                
                for date in dates[:10]:  # Limit to avoid noise
                    election = {
                        'election_id': self.generate_id(url, date),
                        'name': f"Election on {date}",
                        'jurisdiction': self._infer_jurisdiction_from_url(url),
                        'level': self._infer_level_from_url(url),
                        'scheduled_date': date,
                        'election_type': None,
                        'source_url': url,
                        'last_updated': self.get_timestamp(),
                    }
                    elections.append(election)
            
        except Exception as e:
            self.logger.error(f"Error parsing election schedule from {url}: {e}")
        
        return elections
    
    def _scrape_election_results_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape single page for election results.
        
        Args:
            url: Page URL
            
        Returns:
            List of result records
        """
        results = []
        
        try:
            response = self.http.get(url)
            if not response:
                return results
            
            soup = parse_html(response.text)
            
            # Generate election ID for this results page
            election_id = self.generate_id(url)
            
            # Look for results tables
            tables = soup.find_all('table')
            for table in tables:
                results.extend(self._parse_results_table(table, election_id, url))
            
        except Exception as e:
            self.logger.error(f"Error parsing results from {url}: {e}")
        
        return results
    
    def _parse_election_table(self, table, source_url: str) -> List[Dict[str, Any]]:
        """Parse election info from table."""
        elections = []
        
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            # Extract text from cells
            cell_texts = [extract_text(cell) for cell in cells]
            
            # Look for date in any cell
            date = None
            name = None
            
            for text in cell_texts:
                if not date:
                    date = extract_date_from_text(text)
                if not name and len(text) > 5:
                    name = text
            
            if date or name:
                election = {
                    'election_id': self.generate_id(source_url, name or date or ''),
                    'name': name or f"Election on {date}" if date else "Unknown Election",
                    'jurisdiction': self._infer_jurisdiction_from_url(source_url),
                    'level': self._infer_level_from_url(source_url),
                    'scheduled_date': date,
                    'election_type': None,
                    'source_url': source_url,
                    'last_updated': self.get_timestamp(),
                }
                elections.append(election)
        
        return elections
    
    def _parse_election_list(self, lst, source_url: str) -> List[Dict[str, Any]]:
        """Parse election info from list."""
        elections = []
        
        items = lst.find_all('li')
        
        for item in items:
            text = extract_text(item)
            date = extract_date_from_text(text)
            
            if date or len(text) > 10:
                election = {
                    'election_id': self.generate_id(source_url, text),
                    'name': clean_text(text[:200]),
                    'jurisdiction': self._infer_jurisdiction_from_url(source_url),
                    'level': self._infer_level_from_url(source_url),
                    'scheduled_date': date,
                    'election_type': None,
                    'source_url': source_url,
                    'last_updated': self.get_timestamp(),
                }
                elections.append(election)
        
        return elections
    
    def _parse_results_table(
        self,
        table,
        election_id: str,
        source_url: str
    ) -> List[Dict[str, Any]]:
        """Parse election results from table."""
        results = []
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return results
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            cell_texts = [extract_text(cell) for cell in cells]
            
            # Basic extraction - assumes name in first column
            candidate_name = cell_texts[0] if cell_texts else ""
            
            # Try to find votes (look for numbers)
            votes = None
            for text in cell_texts:
                if text.replace(',', '').isdigit():
                    votes = int(text.replace(',', ''))
                    break
            
            if candidate_name:
                result = {
                    'election_id': election_id,
                    'candidate_name': clean_text(candidate_name),
                    'official_id': None,  # TODO: Match with officials
                    'party': None,
                    'votes': votes,
                    'vote_percentage': None,
                    'result': 'pending',
                    'rank': None,
                    'source_url': source_url,
                    'last_updated': self.get_timestamp(),
                }
                results.append(result)
        
        return results
    
    def _extract_all_dates(self, text: str) -> List[str]:
        """Extract all dates from text."""
        import re
        
        dates = []
        
        # Japanese date pattern
        pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        for match in re.finditer(pattern, text):
            year, month, day = match.groups()
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            dates.append(date_str)
        
        return dates
    
    def _infer_jurisdiction_from_url(self, url: str) -> str:
        """Infer jurisdiction from URL."""
        # Look for prefecture names in URL
        prefectures = {
            'tokyo': '東京都', 'osaka': '大阪府', 'kyoto': '京都府',
            'hokkaido': '北海道', 'aichi': '愛知県', 'kanagawa': '神奈川県',
        }
        
        url_lower = url.lower()
        for key, name in prefectures.items():
            if key in url_lower or name in url:
                return name
        
        return "Unknown"
    
    def _infer_level_from_url(self, url: str) -> str:
        """Infer election level from URL."""
        if 'soumu.go.jp' in url or 'national' in url.lower():
            return 'national'
        elif 'pref' in url or 'prefectural' in url.lower():
            return 'prefectural'
        elif 'city' in url or 'municipal' in url.lower():
            return 'municipal'
        
        return 'national'  # Default
    
    def scrape(
        self,
        urls: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Main scrape method (required by BaseScraper).
        Scrapes both election schedules and results.
        
        Args:
            urls: List of URLs to scrape (uses config if None)
            limit: Maximum number to scrape
            
        Returns:
            Combined list of election schedules and results
        """
        # Scrape schedules
        schedules = self.scrape_schedules(urls=urls, limit=limit)
        
        # Scrape results
        results = self.scrape_results(urls=urls, limit=limit)
        
        # Combine and return
        self.results = schedules
        self.election_results = results
        
        self.logger.info(
            f"Scraping complete. Collected {len(schedules)} schedules "
            f"and {len(results)} results"
        )
        
        return schedules
    
    def get_election_results(self) -> List[Dict[str, Any]]:
        """Get collected election results."""
        return self.election_results
