"""
Enhanced Municipal Scraper - Professional grade scraper for Japanese municipal websites
Extracts comprehensive information about assembly members including:
- Names, Political parties, Regions, Ages, Terms, Social media, Official websites
"""

import re
import logging
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from datetime import datetime

from src.scrapers.base import BaseScraper
from src.utils.parsers import parse_html


class EnhancedMunicipalScraper(BaseScraper):
    """
    Professional municipal website scraper with comprehensive data extraction.
    Designed to handle various HTML structures and extract detailed official information.
    """
    
    # Keywords for finding assembly member list pages
    LIST_PAGE_KEYWORDS = [
        '議員一覧', '議員名簿', '議会議員', '議員紹介', '議員情報',
        '市議会議員', '区議会議員', '町議会議員', '村議会議員',
        '県議会議員', '都議会議員', '府議会議員', '道議会議員',
        '議員プロフィール', '議員の紹介',
        'council', 'assembly', 'member', 'legislator'
    ]
    
    # Japanese name patterns (family name + given name)
    NAME_PATTERNS = [
        r'[\u4e00-\u9fff]{1,5}\s*[\u4e00-\u9fff]{1,4}',  # Kanji: 山田太郎
        r'[\u3040-\u309f]{2,8}',  # Hiragana: やまだたろう
        r'[\u30a0-\u30ff]{2,8}',  # Katakana: ヤマダタロウ
    ]
    
    # Political party keywords
    PARTY_KEYWORDS = [
        '自民党', '自由民主党', '立憲民主党', '公明党', '共産党', '日本共産党',
        '国民民主党', '維新', '日本維新の会', '社民党', '社会民主党',
        'れいわ', 'れいわ新選組', 'NHK党', '無所属', '市民', '県民', '都民'
    ]
    
    # Age/birthday patterns
    AGE_PATTERNS = [
        r'(\d{1,2})歳',  # 45歳
        r'年齢[：:]\s*(\d{1,2})',  # 年齢：45
        r'(\d{4})年(\d{1,2})月(\d{1,2})日生',  # 1970年5月15日生
        r'昭和(\d{1,2})年',  # 昭和45年
        r'平成(\d{1,2})年',  # 平成5年
    ]
    
    # Election count patterns
    ELECTION_PATTERNS = [
        r'(\d+)期',  # 3期
        r'(\d+)回当選',  # 3回当選
        r'当選回数[：:]\s*(\d+)',  # 当選回数：3
    ]
    
    # Social media patterns
    SOCIAL_PATTERNS = {
        'twitter': [
            r'twitter\.com/([a-zA-Z0-9_]+)',
            r'x\.com/([a-zA-Z0-9_]+)',
        ],
        'facebook': [
            r'facebook\.com/([a-zA-Z0-9._]+)',
            r'fb\.com/([a-zA-Z0-9._]+)',
        ],
        'instagram': [
            r'instagram\.com/([a-zA-Z0-9._]+)',
        ],
        'youtube': [
            r'youtube\.com/(c/|channel/|user/)?([a-zA-Z0-9_-]+)',
        ],
        'line': [
            r'line\.me/R/ti/p/(@[a-zA-Z0-9_]+)',
        ]
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced municipal scraper."""
        super().__init__(*args, **kwargs)
        self.visited_urls: Set[str] = set()
        self.logger = logging.getLogger(__name__)
    
    def scrape(self, url: str) -> List[Dict[str, Any]]:
        """Required by BaseScraper - delegates to scrape_municipality."""
        return self.scrape_municipality(url)
    
    def scrape_municipality(
        self,
        base_url: str,
        municipality_name: Optional[str] = None,
        prefecture: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape comprehensive information about assembly members.
        
        Args:
            base_url: Municipality website URL
            municipality_name: Name of municipality
            prefecture: Prefecture name
            
        Returns:
            List of official records with detailed information
        """
        self.logger.info(f"🏛️  Scraping municipality: {municipality_name or base_url}")
        self.visited_urls.clear()
        
        officials = []
        
        try:
            # Step 1: Find official list pages
            list_pages = self._find_official_list_pages(base_url)
            
            if not list_pages:
                self.logger.warning(f"⚠️  No official list pages found on {base_url}")
                return []
            
            self.logger.info(f"✓ Found {len(list_pages)} potential list pages")
            
            # Step 2: Extract officials from each page
            for page_url in list_pages[:5]:  # Limit to top 5 pages
                try:
                    self.logger.info(f"📄 Extracting from: {page_url}")
                    page_officials = self._extract_officials_from_page(
                        page_url,
                        municipality_name,
                        prefecture
                    )
                    
                    if page_officials:
                        self.logger.info(f"  → Found {len(page_officials)} officials")
                        officials.extend(page_officials)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to extract from {page_url}: {e}")
                    continue
            
            # Step 3: Deduplicate by name
            officials = self._deduplicate_officials(officials)
            
            # Step 4: Validate and clean data
            officials = self._validate_officials(officials)
            
            self.logger.info(f"✅ Extracted {len(officials)} officials from {municipality_name or base_url}")
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping {municipality_name or base_url}: {e}")
            return []
        
        return officials
    
    def _find_official_list_pages(self, base_url: str, max_depth: int = 2) -> List[str]:
        """Find pages that contain assembly member lists."""
        list_pages = []
        
        try:
            response = self.http.get(base_url)
            if not response:
                return []
            
            soup = parse_html(response.text)
            if not soup:
                return []
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if link text contains keywords
                if any(keyword in text for keyword in self.LIST_PAGE_KEYWORDS):
                    full_url = urljoin(base_url, href)
                    
                    # Avoid duplicates and external sites
                    if full_url not in list_pages and self._is_same_domain(base_url, full_url):
                        list_pages.append(full_url)
            
            # If no specific pages found, try the base URL
            if not list_pages:
                list_pages.append(base_url)
            
        except Exception as e:
            self.logger.error(f"Error finding list pages: {e}")
            list_pages.append(base_url)  # Fallback to base URL
        
        return list_pages
    
    def _extract_officials_from_page(
        self,
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract detailed official information from a page."""
        officials = []
        
        try:
            response = self.http.get(page_url)
            if not response:
                return []
            
            soup = parse_html(response.text)
            if not soup:
                return []
            
            # Try multiple extraction strategies
            strategies = [
                self._extract_from_table,
                self._extract_from_list,
                self._extract_from_cards,
                self._extract_from_divs,
            ]
            
            for strategy in strategies:
                try:
                    results = strategy(soup, page_url, municipality_name, prefecture)
                    if results and len(results) > 0:
                        # Filter out navigation items
                        valid_results = [r for r in results if self._is_valid_official(r)]
                        if valid_results:
                            self.logger.info(f"  ✓ Strategy succeeded: {strategy.__name__} ({len(valid_results)} officials)")
                            officials.extend(valid_results)
                            break  # Use first successful strategy
                except Exception as e:
                    self.logger.debug(f"  Strategy {strategy.__name__} failed: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting from page: {e}")
        
        return officials
    
    def _extract_from_table(
        self,
        soup: BeautifulSoup,
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract from HTML table structure."""
        officials = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 1:
                    official = self._parse_official_data(cells, page_url, municipality_name, prefecture)
                    if official:
                        officials.append(official)
        
        return officials
    
    def _extract_from_list(
        self,
        soup: BeautifulSoup,
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract from list structure (ul/ol/li)."""
        officials = []
        
        lists = soup.find_all(['ul', 'ol'])
        
        for lst in lists:
            items = lst.find_all('li')
            
            for item in items:
                # Get all text from the list item
                text = item.get_text(separator=' ', strip=True)
                
                # Extract name
                name = self._extract_name(text)
                if name:
                    official = {
                        'name': name,
                        'municipality': municipality_name or 'Unknown',
                        'prefecture': prefecture or 'Unknown',
                        'source_url': page_url,
                        'extraction_method': 'list',
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Extract additional info
                    official.update(self._extract_additional_info(item, text))
                    
                    officials.append(official)
        
        return officials
    
    def _extract_from_cards(
        self,
        soup: BeautifulSoup,
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract from card-based layouts."""
        officials = []
        
        # Common card class names
        card_selectors = [
            'div.member-card', 'div.official-card', 'div.profile-card',
            'div.member', 'div.official', 'div.profile',
            'article.member', 'article.official',
        ]
        
        for selector in card_selectors:
            cards = soup.select(selector)
            
            for card in cards:
                text = card.get_text(separator=' ', strip=True)
                name = self._extract_name(text)
                
                if name:
                    official = {
                        'name': name,
                        'municipality': municipality_name or 'Unknown',
                        'prefecture': prefecture or 'Unknown',
                        'source_url': page_url,
                        'extraction_method': 'card',
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    official.update(self._extract_additional_info(card, text))
                    officials.append(official)
        
        return officials
    
    def _extract_from_divs(
        self,
        soup: BeautifulSoup,
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Extract from div-based layouts."""
        officials = []
        
        # Find divs that might contain official info
        divs = soup.find_all('div', class_=re.compile(r'(member|official|profile|giin)', re.I))
        
        for div in divs:
            text = div.get_text(separator=' ', strip=True)
            name = self._extract_name(text)
            
            if name:
                official = {
                    'name': name,
                    'municipality': municipality_name or 'Unknown',
                    'prefecture': prefecture or 'Unknown',
                    'source_url': page_url,
                    'extraction_method': 'div',
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                official.update(self._extract_additional_info(div, text))
                officials.append(official)
        
        return officials
    
    def _parse_official_data(
        self,
        cells: List[Tag],
        page_url: str,
        municipality_name: Optional[str],
        prefecture: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Parse official data from table cells."""
        if not cells:
            return None
        
        # Combine all cell text
        full_text = ' '.join([cell.get_text(strip=True) for cell in cells])
        
        # Extract name from first cell
        name = self._extract_name(cells[0].get_text(strip=True))
        if not name:
            return None
        
        official = {
            'name': name,
            'municipality': municipality_name or 'Unknown',
            'prefecture': prefecture or 'Unknown',
            'source_url': page_url,
            'extraction_method': 'table',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extract additional info from all cells
        official.update(self._extract_additional_info(cells[0].parent, full_text))
        
        return official
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract Japanese name from text."""
        if not text or len(text) < 2:
            return None
        
        # Try each name pattern
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                name = match.group(0).strip()
                
                # Validate it's actually a name (not a common word)
                if self._is_likely_name(name):
                    return name
        
        return None
    
    def _is_likely_name(self, text: str) -> bool:
        """Check if text is likely a person's name."""
        # Exclude common non-name words
        excluded_words = [
            '議員', '市議', '区議', '町議', '村議', '県議', '都議', '府議', '道議',
            '議長', '副議長', '委員長', '委員', '会長', '副会長',
            '住民', '登録', '相談', '窓口', '受付', '案内', '情報', '一覧', '名簿',
            '上下水道', '浄化槽', '除雪', '道路', '河川', '動物', 'ペット',
            '墓地', '墓園', '消費', '生活', 'くらし', '住まい', '土地'
        ]
        
        for excluded in excluded_words:
            if excluded in text:
                return False
        
        # Name should be 2-8 characters
        if len(text) < 2 or len(text) > 8:
            return False
        
        return True
    
    def _extract_additional_info(self, element: Tag, text: str) -> Dict[str, Any]:
        """Extract additional information like party, age, social media."""
        info = {}
        
        # Extract political party
        party = self._extract_party(text)
        if party:
            info['party'] = party
        
        # Extract age
        age = self._extract_age(text)
        if age:
            info['age'] = age
        
        # Extract election count
        elections = self._extract_election_count(text)
        if elections:
            info['election_count'] = elections
        
        # Extract region/constituency
        region = self._extract_region(text)
        if region:
            info['region'] = region
        
        # Extract social media
        social = self._extract_social_media(element)
        if social:
            info.update(social)
        
        # Extract official website
        website = self._extract_official_website(element)
        if website:
            info['official_website'] = website
        
        return info
    
    def _extract_party(self, text: str) -> Optional[str]:
        """Extract political party from text."""
        for party in self.PARTY_KEYWORDS:
            if party in text:
                return party
        return None
    
    def _extract_age(self, text: str) -> Optional[int]:
        """Extract age from text."""
        for pattern in self.AGE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    if '歳' in pattern:
                        return int(match.group(1))
                    elif '年齢' in pattern:
                        return int(match.group(1))
                    # Handle birth dates if needed
                except:
                    continue
        return None
    
    def _extract_election_count(self, text: str) -> Optional[int]:
        """Extract number of times elected."""
        for pattern in self.ELECTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        return None
    
    def _extract_region(self, text: str) -> Optional[str]:
        """Extract electoral district/region."""
        # Common region patterns
        region_patterns = [
            r'([1-9]区)',  # 1区, 2区
            r'([東西南北中][部区])',  # 東部, 西区
            r'([あ-ん]{2,5}区)',  # ひらがな区名
        ]
        
        for pattern in region_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_social_media(self, element: Tag) -> Dict[str, str]:
        """Extract social media URLs."""
        social = {}
        
        # Find all links in element
        links = element.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            for platform, patterns in self.SOCIAL_PATTERNS.items():
                for pattern in patterns:
                    match = re.search(pattern, href, re.I)
                    if match:
                        if platform == 'youtube':
                            social['youtube'] = f"https://youtube.com/{match.group(2)}"
                        else:
                            social[platform] = href
                        break
        
        return social
    
    def _extract_official_website(self, element: Tag) -> Optional[str]:
        """Extract official website URL."""
        links = element.find_all('a', href=True)
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Look for keywords indicating official site
            if any(keyword in text for keyword in ['公式', 'ホームページ', 'HP', 'Website', 'Official']):
                return href
            
            # Check if it's an external personal site
            if href.startswith('http') and not any(x in href for x in ['twitter', 'facebook', 'instagram', 'youtube']):
                return href
        
        return None
    
    def _is_valid_official(self, official: Dict[str, Any]) -> bool:
        """Validate that extracted data is actually an official."""
        name = official.get('name', '')
        
        # Must have a name
        if not name or len(name) < 2:
            return False
        
        # Check if it's likely a name
        if not self._is_likely_name(name):
            return False
        
        return True
    
    def _deduplicate_officials(self, officials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate officials by name."""
        seen_names = set()
        unique_officials = []
        
        for official in officials:
            name = official.get('name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                unique_officials.append(official)
        
        return unique_officials
    
    def _validate_officials(self, officials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Final validation and cleanup of official data."""
        validated = []
        
        for official in officials:
            # Ensure required fields
            if not official.get('name'):
                continue
            
            # Set defaults for missing fields
            official.setdefault('party', '')
            official.setdefault('age', '')
            official.setdefault('region', '')
            official.setdefault('election_count', '')
            official.setdefault('twitter', '')
            official.setdefault('facebook', '')
            official.setdefault('instagram', '')
            official.setdefault('official_website', '')
            
            validated.append(official)
        
        return validated
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2 or domain2.endswith(domain1) or domain1.endswith(domain2)
        except:
            return False
