"""
Smart Municipal Scraper - Adaptive scraper for municipal websites.
Automatically detects and extracts official lists from diverse HTML structures.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .base import BaseScraper
from ..utils.parsers import (
    parse_html,
    extract_text,
    clean_text,
    normalize_url,
)


class SmartMunicipalScraper(BaseScraper):
    """
    Intelligent scraper that adapts to different municipal website structures.
    Uses pattern recognition to find official lists automatically.
    """
    
    # Keywords that indicate official lists pages (Japanese)
    LIST_PAGE_KEYWORDS = [
        '議員一覧', '議員名簿', '議会議員', '議員紹介',
        '市議会議員', '区議会議員', '町議会議員', '村議会議員',
        '県議会議員', '都議会議員', '府議会議員', '道議会議員',
        '首長', '市長', '区長', '町長', '村長',
        '知事', '副知事',
        'member', 'council', 'assembly', 'legislator'
    ]
    
    # HTML patterns that indicate official data
    OFFICIAL_NAME_PATTERNS = [
        r'[\u4e00-\u9fff]{2,4}\s*[\u4e00-\u9fff]{1,4}',  # Kanji name pattern
        r'[ぁ-ん]{2,}',  # Hiragana
        r'[ァ-ヴ]{2,}',  # Katakana
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize smart municipal scraper."""
        super().__init__(*args, **kwargs)
        self.visited_urls: Set[str] = set()
    
    def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape method required by BaseScraper.
        
        Args:
            url: URL to scrape
            
        Returns:
            List of official records
        """
        return self.scrape_municipality(url)
    
    def scrape_municipality(
        self,
        base_url: str,
        municipality_name: Optional[str] = None,
        prefecture: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape all officials from a municipal website.
        
        Args:
            base_url: Municipality website URL
            municipality_name: Name of municipality
            prefecture: Prefecture name
            
        Returns:
            List of official records
        """
        self.logger.info(f"Scraping municipality: {municipality_name or base_url}")
        self.visited_urls.clear()
        
        officials = []
        
        try:
            # Step 1: Find pages that might contain official lists
            list_pages = self._find_official_list_pages(base_url)
            
            if not list_pages:
                self.logger.warning(f"No official list pages found on {base_url}")
                return []
            
            self.logger.info(f"Found {len(list_pages)} potential list pages")
            
            # Step 2: Extract officials from each list page
            for page_url in list_pages:
                try:
                    page_officials = self._extract_officials_from_page(
                        page_url,
                        municipality_name,
                        prefecture
                    )
                    officials.extend(page_officials)
                except Exception as e:
                    self.logger.error(f"Failed to extract from {page_url}: {e}")
                    continue
            
            # Step 3: Deduplicate by name
            officials = self._deduplicate_officials(officials)
            
            self.logger.info(f"Extracted {len(officials)} officials from {municipality_name or base_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to scrape {base_url}: {e}", exc_info=True)
        
        return officials
    
    def _find_official_list_pages(self, base_url: str, max_depth: int = 2) -> List[str]:
        """
        Find pages that likely contain official lists.
        
        Args:
            base_url: Starting URL
            max_depth: Maximum crawl depth
            
        Returns:
            List of potential list page URLs
        """
        list_pages = []
        to_visit = [(base_url, 0)]
        self.visited_urls.add(base_url)
        
        while to_visit:
            url, depth = to_visit.pop(0)
            
            if depth > max_depth:
                continue
            
            try:
                response = self.http.get(url)
                if not response:
                    continue
                
                soup = parse_html(response.text)
                
                # Check if current page is a list page
                if self._is_list_page(soup):
                    list_pages.append(url)
                
                # Find links to potential list pages (only if not too deep)
                if depth < max_depth:
                    links = self._find_relevant_links(soup, url)
                    for link in links:
                        if link not in self.visited_urls:
                            self.visited_urls.add(link)
                            to_visit.append((link, depth + 1))
                
            except Exception as e:
                self.logger.debug(f"Error visiting {url}: {e}")
                continue
        
        return list_pages
    
    def _is_list_page(self, soup: BeautifulSoup) -> bool:
        """Check if page contains official list."""
        page_text = soup.get_text().lower()
        
        # Check for list keywords
        for keyword in self.LIST_PAGE_KEYWORDS:
            if keyword.lower() in page_text:
                return True
        
        # Check for table structures with multiple officials
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) >= 3:  # At least header + 2 officials
                # Check if table contains names
                table_text = table.get_text()
                name_matches = sum(1 for pattern in self.OFFICIAL_NAME_PATTERNS 
                                 if re.search(pattern, table_text))
                if name_matches >= 2:
                    return True
        
        return False
    
    def _find_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links that might lead to official lists."""
        relevant_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().strip().lower()
            
            # Check if link text contains keywords
            is_relevant = any(keyword.lower() in link_text for keyword in self.LIST_PAGE_KEYWORDS)
            
            if is_relevant:
                full_url = urljoin(base_url, href)
                # Only follow links on same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    relevant_links.append(full_url)
        
        return relevant_links
    
    def _extract_officials_from_page(
        self,
        url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract official data from a single page."""
        response = self.http.get(url)
        if not response:
            return []
        
        soup = parse_html(response.text)
        officials = []
        
        # Try different extraction strategies
        strategies = [
            self._extract_from_table,
            self._extract_from_list,
            self._extract_from_divs,
        ]
        
        for strategy in strategies:
            try:
                results = strategy(soup, url, municipality_name, prefecture)
                if results:
                    officials.extend(results)
                    self.logger.debug(f"Strategy {strategy.__name__} found {len(results)} officials")
            except Exception as e:
                self.logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        return officials
    
    def _extract_from_table(
        self,
        soup: BeautifulSoup,
        url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract officials from HTML tables."""
        officials = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            
            # Skip tables with too few rows
            if len(rows) < 2:
                continue
            
            # Try to find header row
            header_row = rows[0]
            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
            
            # Find name column index
            name_col_idx = self._find_name_column(headers)
            
            # Process data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) == 0:
                    continue
                
                # Extract name
                name = None
                if name_col_idx is not None and name_col_idx < len(cells):
                    name = clean_text(cells[name_col_idx].get_text())
                else:
                    # Fallback: first cell with Japanese characters
                    for cell in cells:
                        text = clean_text(cell.get_text())
                        if self._looks_like_name(text):
                            name = text
                            break
                
                if name:
                    official_data = {
                        'official_id': self.generate_id(f"{url}_{name}"),
                        'name': name,
                        'municipality': municipality_name,
                        'prefecture': prefecture,
                        'source_url': url,
                        'extraction_method': 'table',
                        'last_updated': self.get_timestamp(),
                    }
                    
                    # Try to extract additional info from other cells
                    for idx, cell in enumerate(cells):
                        cell_text = clean_text(cell.get_text())
                        
                        # Age detection
                        age_match = re.search(r'(\d{2})歳', cell_text)
                        if age_match:
                            official_data['age'] = int(age_match.group(1))
                        
                        # Party/faction detection
                        if any(party in cell_text for party in ['党', '会派', '無所属']):
                            official_data['faction'] = cell_text
                    
                    officials.append(official_data)
        
        return officials
    
    def _extract_from_list(
        self,
        soup: BeautifulSoup,
        url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract officials from HTML lists (ul, ol)."""
        officials = []
        
        for list_tag in soup.find_all(['ul', 'ol']):
            items = list_tag.find_all('li')
            
            if len(items) < 2:
                continue
            
            for item in items:
                text = clean_text(item.get_text())
                
                if self._looks_like_name(text):
                    # Extract just the name part
                    name = self._extract_name_from_text(text)
                    
                    if name:
                        officials.append({
                            'official_id': self.generate_id(f"{url}_{name}"),
                            'name': name,
                            'municipality': municipality_name,
                            'prefecture': prefecture,
                            'source_url': url,
                            'extraction_method': 'list',
                            'last_updated': self.get_timestamp(),
                        })
        
        return officials
    
    def _extract_from_divs(
        self,
        soup: BeautifulSoup,
        url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract officials from div-based layouts."""
        officials = []
        
        # Look for divs with common class names
        common_classes = ['member', 'official', 'council', 'giin', 'list-item']
        
        for class_name in common_classes:
            divs = soup.find_all('div', class_=re.compile(class_name, re.I))
            
            for div in divs:
                text = clean_text(div.get_text())
                
                if self._looks_like_name(text):
                    name = self._extract_name_from_text(text)
                    
                    if name:
                        officials.append({
                            'official_id': self.generate_id(f"{url}_{name}"),
                            'name': name,
                            'municipality': municipality_name,
                            'prefecture': prefecture,
                            'source_url': url,
                            'extraction_method': 'div',
                            'last_updated': self.get_timestamp(),
                        })
        
        return officials
    
    def _find_name_column(self, headers: List[str]) -> Optional[int]:
        """Find which column contains names."""
        name_keywords = ['名前', '氏名', '議員名', 'name', '名']
        
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in name_keywords):
                return idx
        
        return None
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a Japanese name."""
        if len(text) < 2 or len(text) > 20:
            return False
        
        # Check for kanji patterns
        kanji_pattern = r'[\u4e00-\u9fff]{2,6}'
        if re.search(kanji_pattern, text):
            return True
        
        return False
    
    def _extract_name_from_text(self, text: str) -> Optional[str]:
        """Extract name from text that may contain other info."""
        # Try to match kanji name pattern
        match = re.search(r'[\u4e00-\u9fff]{2,4}\s*[\u4e00-\u9fff]{1,4}', text)
        if match:
            return match.group(0).strip()
        
        # Fallback: return cleaned text if short enough
        if len(text) <= 20:
            return text
        
        return None
    
    def _deduplicate_officials(self, officials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate officials based on name."""
        seen_names = set()
        unique_officials = []
        
        for official in officials:
            name = official.get('name')
            if name and name not in seen_names:
                seen_names.add(name)
                unique_officials.append(official)
        
        return unique_officials
