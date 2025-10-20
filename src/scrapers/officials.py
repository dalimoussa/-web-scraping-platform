"""
Officials scraper - extracts public official information from websites.
Collects: name, age, faction, promises, blog, SNS links.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseScraper
from ..utils.parsers import (
    parse_html,
    extract_text,
    find_sns_links,
    extract_age_from_text,
    normalize_url,
    clean_text,
)
from ..core.config import load_sources


class OfficialsScraper(BaseScraper):
    """Scraper for public official information."""
    
    def __init__(self, *args, **kwargs):
        """Initialize officials scraper."""
        super().__init__(*args, **kwargs)
        self.sources = load_sources()
        self.sns_patterns = self.config.sns_patterns
    
    def scrape(
        self,
        urls: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape official information from websites.
        
        Args:
            urls: List of URLs to scrape (uses config if None)
            limit: Maximum number of officials to scrape
            
        Returns:
            List of official records
        """
        self.clear_results()
        
        # Get URLs from config if not provided
        if urls is None:
            urls = self._get_seed_urls()
        
        if not urls:
            self.logger.warning("No URLs to scrape")
            return []
        
        self.logger.info(f"Starting scrape of {len(urls)} official websites")
        
        # Apply limit
        if limit:
            urls = urls[:limit]
        
        # Scrape each URL
        for idx, url in enumerate(urls, 1):
            try:
                self.logger.info(f"Scraping {idx}/{len(urls)}: {url}")
                official_data = self._scrape_official_page(url)
                
                if official_data:
                    self.add_result(official_data)
                    
                self.log_progress(idx, len(urls), "websites")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Scraping complete. Collected {len(self.results)} officials")
        return self.get_results()
    
    def _get_seed_urls(self) -> List[str]:
        """
        Get seed URLs from sources config.
        
        Returns:
            List of official website URLs
        """
        urls = []
        
        # Get from sources.yaml
        official_websites = self.sources.get('official_websites', {})
        
        for level in ['national', 'prefectural', 'municipal']:
            level_data = official_websites.get(level, [])
            for item in level_data:
                if isinstance(item, dict) and 'url' in item:
                    urls.append(item['url'])
                elif isinstance(item, str):
                    urls.append(item)
        
        return urls
    
    def _scrape_official_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape single official page.
        
        Args:
            url: Official website URL
            
        Returns:
            Official data dict or None
        """
        try:
            response = self.http.get(url)
            if not response:
                return None
            
            soup = parse_html(response.text)
            
            # Extract data
            official_data = {
                'official_id': self.generate_id(url),
                'name': self._extract_name(soup, url),
                'name_kana': self._extract_name_kana(soup),
                'age': self._extract_age(soup),
                'faction': self._extract_faction(soup),
                'office_type': self._infer_office_type(soup, url),
                'jurisdiction': self._extract_jurisdiction(soup),
                'promises_text': self._extract_promises(soup),
                'promises_url': self._find_promises_url(soup, url),
                'website_url': url,
                'blog_url': self._find_blog_url(soup, url),
                'source_url': url,
                'last_updated': self.get_timestamp(),
            }
            
            # Also collect SNS data separately
            sns_data = self._extract_sns_links(soup, official_data['official_id'])
            if sns_data:
                # Store SNS data for later export
                if not hasattr(self, 'sns_results'):
                    self.sns_results = []
                self.sns_results.extend(sns_data)
            
            return official_data
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _extract_name(self, soup, url: str) -> str:
        """Extract official name."""
        # Try multiple strategies
        
        # 1. Look for common name selectors
        selectors = [
            'h1.name',
            'h1',
            '.profile-name',
            '.name',
            'meta[property="og:title"]',
        ]
        
        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    name = element.get('content', '')
                    if name:
                        return clean_text(name)
            else:
                element = soup.select_one(selector)
                if element:
                    name = extract_text(element)
                    if name and len(name) < 50:  # Sanity check
                        return clean_text(name)
        
        # 2. Try title tag
        title = soup.find('title')
        if title:
            title_text = extract_text(title)
            # Remove common suffixes
            title_text = title_text.split('|')[0].split('-')[0].strip()
            if title_text:
                return clean_text(title_text)
        
        # Fallback: use domain
        return url.split('//')[-1].split('/')[0]
    
    def _extract_name_kana(self, soup) -> Optional[str]:
        """Extract phonetic name (furigana)."""
        selectors = ['.name-kana', '.kana', 'ruby rt']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return clean_text(extract_text(element))
        
        return None
    
    def _extract_age(self, soup) -> Optional[int]:
        """Extract age from page."""
        # Get all text and search for age patterns
        page_text = soup.get_text()
        return extract_age_from_text(page_text)
    
    def _extract_faction(self, soup) -> Optional[str]:
        """Extract political faction/party."""
        # Common patterns for party/faction
        keywords = ['政党', '会派', '所属', '党', 'party', 'faction']
        
        for keyword in keywords:
            # Look for elements containing keyword
            elements = soup.find_all(text=lambda t: t and keyword in t.lower())
            
            for element in elements:
                parent = element.parent
                if parent:
                    text = extract_text(parent)
                    # Extract faction name (usually after the keyword)
                    parts = text.split(keyword)
                    if len(parts) > 1:
                        faction = parts[1].split()[0] if parts[1].split() else ""
                        if faction and len(faction) < 30:
                            return clean_text(faction)
        
        return None
    
    def _infer_office_type(self, soup, url: str) -> Optional[str]:
        """Infer office type (national/prefectural/municipal)."""
        page_text = soup.get_text().lower()
        
        # Keywords for each level
        if any(kw in page_text for kw in ['衆議院', '参議院', '国会議員', 'house of representatives', 'diet']):
            return 'national'
        elif any(kw in page_text for kw in ['都議', '道議', '府議', '県議', 'prefectural']):
            return 'prefectural'
        elif any(kw in page_text for kw in ['市議', '区議', '町議', '村議', 'municipal', 'city council']):
            return 'municipal'
        
        return None
    
    def _extract_jurisdiction(self, soup) -> Optional[str]:
        """Extract geographic jurisdiction."""
        # Look for prefecture/city names
        prefectures = [
            '北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島',
            '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川',
            '新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜',
            '静岡', '愛知', '三重', '滋賀', '京都', '大阪', '兵庫',
            '奈良', '和歌山', '鳥取', '島根', '岡山', '広島', '山口',
            '徳島', '香川', '愛媛', '高知', '福岡', '佐賀', '長崎',
            '熊本', '大分', '宮崎', '鹿児島', '沖縄'
        ]
        
        page_text = soup.get_text()
        
        for pref in prefectures:
            if pref in page_text:
                return pref
        
        return None
    
    def _extract_promises(self, soup) -> Optional[str]:
        """Extract campaign promises text."""
        # Look for promises/manifesto sections
        keywords = ['公約', 'マニフェスト', '政策', 'pledge', 'manifesto', 'policy']
        
        for keyword in keywords:
            # Find headings with keyword
            headings = soup.find_all(['h2', 'h3', 'h4'], text=lambda t: t and keyword in t)
            
            for heading in headings:
                # Get following content
                content = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        break
                    text = extract_text(sibling)
                    if text:
                        content.append(text)
                
                if content:
                    promises_text = " ".join(content)[:5000]  # Limit length
                    return clean_text(promises_text)
        
        return None
    
    def _find_promises_url(self, soup, base_url: str) -> Optional[str]:
        """Find link to promises/manifesto page."""
        keywords = ['公約', 'マニフェスト', '政策', 'pledge', 'manifesto', 'policy']
        
        for a_tag in soup.find_all('a', href=True):
            link_text = extract_text(a_tag).lower()
            href = a_tag['href']
            
            if any(kw in link_text for kw in keywords):
                return normalize_url(href, base_url)
        
        return None
    
    def _find_blog_url(self, soup, base_url: str) -> Optional[str]:
        """Find blog URL."""
        keywords = ['ブログ', 'blog', '日記', 'diary']
        
        for a_tag in soup.find_all('a', href=True):
            link_text = extract_text(a_tag).lower()
            href = a_tag['href']
            
            if any(kw in link_text for kw in keywords):
                return normalize_url(href, base_url)
        
        return None
    
    def _extract_sns_links(self, soup, official_id: str) -> List[Dict[str, Any]]:
        """
        Extract SNS profile links.
        
        Args:
            soup: BeautifulSoup object
            official_id: Official ID to link to
            
        Returns:
            List of SNS link records
        """
        sns_links = find_sns_links(soup, self.sns_patterns)
        
        records = []
        for platform, urls in sns_links.items():
            for url in urls:
                # Extract handle from URL
                handle = self._extract_handle_from_url(url, platform)
                
                record = {
                    'official_id': official_id,
                    'platform': platform,
                    'handle': handle,
                    'profile_url': url,
                    'verified': None,  # Cannot determine without API access
                    'follower_count': None,
                    'last_updated': self.get_timestamp(),
                }
                records.append(record)
        
        return records
    
    def _extract_handle_from_url(self, url: str, platform: str) -> Optional[str]:
        """Extract username/handle from SNS URL."""
        import re
        
        patterns = {
            'x': r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
            'instagram': r'instagram\.com/([a-zA-Z0-9_.]+)',
            'facebook': r'(?:facebook\.com|fb\.com)/([a-zA-Z0-9.]+)',
            'youtube': r'youtube\.com/(?:channel/|@|c/)([a-zA-Z0-9_-]+)',
        }
        
        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_sns_results(self) -> List[Dict[str, Any]]:
        """Get collected SNS data."""
        return getattr(self, 'sns_results', [])
