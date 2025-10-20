"""
HTML parsing utilities and helpers.
"""

import re
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from ..core.logger import get_logger


logger = get_logger(__name__)


def parse_html(html: str, parser: str = "lxml") -> BeautifulSoup:
    """
    Parse HTML string to BeautifulSoup object.
    
    Args:
        html: HTML string
        parser: Parser to use (lxml, html.parser)
        
    Returns:
        BeautifulSoup object
    """
    return BeautifulSoup(html, parser)


def extract_text(element: Tag, strip: bool = True) -> str:
    """
    Extract text from BeautifulSoup element.
    
    Args:
        element: BeautifulSoup element
        strip: Whether to strip whitespace
        
    Returns:
        Extracted text
    """
    if element is None:
        return ""
    
    text = element.get_text()
    if strip:
        text = " ".join(text.split())  # Normalize whitespace
    
    return text


def extract_links(soup: BeautifulSoup, base_url: str = "") -> List[str]:
    """
    Extract all links from page.
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative links
        
    Returns:
        List of absolute URLs
    """
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if base_url:
            href = urljoin(base_url, href)
        links.append(href)
    
    return links


def find_sns_links(
    soup: BeautifulSoup,
    patterns: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, List[str]]:
    """
    Find social media links in page.
    
    Args:
        soup: BeautifulSoup object
        patterns: SNS patterns config (from config.yaml)
        
    Returns:
        Dict mapping platform to list of URLs
    """
    if patterns is None:
        # Default patterns
        patterns = {
            'x': {'domains': ['twitter.com', 'x.com']},
            'instagram': {'domains': ['instagram.com']},
            'facebook': {'domains': ['facebook.com', 'fb.com']},
            'youtube': {'domains': ['youtube.com']},
        }
    
    sns_links: Dict[str, List[str]] = {platform: [] for platform in patterns.keys()}
    
    # Find all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].lower()
        
        for platform, config in patterns.items():
            domains = config.get('domains', [])
            
            for domain in domains:
                if domain in href:
                    # Store original (not lowercase) URL
                    original_href = a_tag['href']
                    if original_href not in sns_links[platform]:
                        sns_links[platform].append(original_href)
                    break
    
    return sns_links


def extract_meta_tags(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract meta tags from page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dict of meta tag content
    """
    meta_data = {}
    
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property', '')
        content = meta.get('content', '')
        
        if name and content:
            meta_data[name] = content
    
    return meta_data


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove common control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def extract_age_from_text(text: str) -> Optional[int]:
    """
    Extract age from Japanese text.
    
    Args:
        text: Text containing age information
        
    Returns:
        Age as integer or None
    """
    # Pattern for "XX歳" or "年齢：XX"
    patterns = [
        r'(\d{1,3})歳',
        r'年齢[：:]\s*(\d{1,3})',
        r'Age[：:]\s*(\d{1,3})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            age = int(match.group(1))
            if 0 <= age <= 150:  # Sanity check
                return age
    
    return None


def extract_date_from_text(text: str) -> Optional[str]:
    """
    Extract date from Japanese text.
    
    Args:
        text: Text containing date
        
    Returns:
        Date string in YYYY-MM-DD format or None
    """
    # Pattern for Japanese dates: YYYY年MM月DD日
    pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    match = re.search(pattern, text)
    
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Pattern for Western dates: YYYY-MM-DD or YYYY/MM/DD
    pattern = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
    match = re.search(pattern, text)
    
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None


def is_valid_url(url: str, require_scheme: bool = True) -> bool:
    """
    Check if string is a valid URL.
    
    Args:
        url: URL to validate
        require_scheme: Whether to require http/https scheme
        
    Returns:
        True if valid URL
    """
    try:
        result = urlparse(url)
        
        if require_scheme:
            return all([result.scheme in ('http', 'https'), result.netloc])
        else:
            return bool(result.netloc)
            
    except Exception:
        return False


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize and resolve URL.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative resolution
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    # Resolve relative URLs
    if base_url:
        url = urljoin(base_url, url)
    
    # Remove fragment
    url = url.split('#')[0]
    
    return url.strip()
