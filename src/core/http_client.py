"""
HTTP client with rate limiting, caching, retries, and compliance.
"""

import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests_cache import CachedSession

from ..core.logger import get_logger


class HTTPClient:
    """
    Production-grade HTTP client with:
    - Rate limiting per domain
    - Response caching
    - Automatic retries with exponential backoff
    - robots.txt compliance
    - Configurable timeouts and user agents
    """
    
    def __init__(
        self,
        default_delay: float = 1.5,
        max_retries: int = 3,
        timeout: int = 30,
        respect_robots_txt: bool = True,
        use_cache: bool = True,
        cache_dir: str = "data/cache",
        cache_expire_after: int = 86400,
        user_agent: str = "PublicOfficialsScraper/1.0 (Research)",
    ):
        """
        Initialize HTTP client.
        
        Args:
            default_delay: Seconds between requests to same domain
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            respect_robots_txt: Whether to check robots.txt
            use_cache: Enable response caching
            cache_dir: Cache directory path
            cache_expire_after: Cache expiration in seconds
            user_agent: User-Agent header
        """
        self.logger = get_logger(__name__)
        self.default_delay = default_delay
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent
        
        # Track last request time per domain
        self._last_request_time: Dict[str, float] = {}
        
        # robots.txt parsers per domain
        self._robots_parsers: Dict[str, RobotFileParser] = {}
        
        # Setup session
        if use_cache:
            cache_path = Path(cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            self.session = CachedSession(
                str(cache_path / "http_cache"),
                expire_after=cache_expire_after,
                allowable_methods=('GET', 'HEAD'),
            )
        else:
            self.session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.logger.info(f"HTTPClient initialized: delay={default_delay}s, cache={use_cache}")
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc
    
    def _check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        if not self.respect_robots_txt:
            return True
        
        domain = self._get_domain(url)
        
        # Get or create parser for this domain
        if domain not in self._robots_parsers:
            parser = RobotFileParser()
            robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
            
            try:
                parser.set_url(robots_url)
                parser.read()
                self._robots_parsers[domain] = parser
                self.logger.debug(f"Loaded robots.txt for {domain}")
            except Exception as e:
                self.logger.warning(f"Could not load robots.txt for {domain}: {e}")
                # Allow by default if robots.txt unavailable
                return True
        
        parser = self._robots_parsers[domain]
        can_fetch = parser.can_fetch(self.user_agent, url)
        
        if not can_fetch:
            self.logger.warning(f"robots.txt disallows: {url}")
        
        return can_fetch
    
    def _rate_limit(self, domain: str, delay: Optional[float] = None):
        """
        Enforce rate limiting for domain.
        
        Args:
            domain: Domain to rate limit
            delay: Custom delay (uses default if None)
        """
        delay = delay or self.default_delay
        
        if domain in self._last_request_time:
            elapsed = time.time() - self._last_request_time[domain]
            if elapsed < delay:
                sleep_time = delay - elapsed
                self.logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self._last_request_time[domain] = time.time()
    
    def get(
        self,
        url: str,
        delay: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """
        Perform GET request with rate limiting and compliance.
        
        Args:
            url: URL to fetch
            delay: Custom delay for this request
            headers: Additional headers
            **kwargs: Additional arguments for requests.get
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: On request failure
            PermissionError: If blocked by robots.txt
        """
        # Check robots.txt
        if not self._check_robots_txt(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")
        
        # Rate limit
        domain = self._get_domain(url)
        self._rate_limit(domain, delay)
        
        # Merge headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        # Make request
        self.logger.debug(f"GET {url}")
        
        try:
            response = self.session.get(
                url,
                headers=req_headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            # Auto-detect encoding for Japanese content
            # Many Japanese government sites use Shift_JIS
            if response.apparent_encoding and response.apparent_encoding.upper() in ['SHIFT_JIS', 'SHIFT-JIS', 'CP932']:
                response.encoding = response.apparent_encoding
                self.logger.debug(f"Using encoding: {response.encoding}")
            elif 'shift_jis' in response.text.lower()[:500] or 'shift-jis' in response.text.lower()[:500]:
                # Check if HTML declares Shift_JIS in meta tag or XML header
                response.encoding = 'shift_jis'
                self.logger.debug(f"Detected Shift_JIS in HTML, using encoding: {response.encoding}")
            
            # Log cache status if available
            if hasattr(response, 'from_cache'):
                cache_status = "HIT" if response.from_cache else "MISS"
                self.logger.debug(f"Cache {cache_status}: {url}")
            
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    def get_safe(
        self,
        url: str,
        default: Optional[Any] = None,
        **kwargs: Any
    ) -> Optional[requests.Response]:
        """
        Safe GET that returns None on failure instead of raising.
        
        Args:
            url: URL to fetch
            default: Default value on failure
            **kwargs: Additional arguments
            
        Returns:
            Response or default value
        """
        try:
            return self.get(url, **kwargs)
        except Exception as e:
            self.logger.warning(f"Safe GET failed for {url}: {e}")
            return default
    
    def clear_cache(self):
        """Clear HTTP cache."""
        if isinstance(self.session, CachedSession):
            self.session.cache.clear()
            self.logger.info("HTTP cache cleared")
    
    def close(self):
        """Close session and cleanup."""
        self.session.close()
        self.logger.info("HTTPClient closed")
