"""
Advanced HTTP client with JavaScript rendering support.
Uses Playwright for JS-heavy sites when needed.
"""

from typing import Optional
import re

from .http_client import HTTPClient
from ..core.logger import get_logger


class AdvancedHTTPClient(HTTPClient):
    """
    Enhanced HTTP client with JavaScript rendering capabilities.
    Falls back to Playwright for JS-heavy sites.
    """
    
    def __init__(self, *args, enable_js_rendering: bool = False, **kwargs):
        """
        Initialize advanced HTTP client.
        
        Args:
            enable_js_rendering: Enable Playwright for JS rendering
            *args, **kwargs: Passed to HTTPClient
        """
        super().__init__(*args, **kwargs)
        self.enable_js_rendering = enable_js_rendering
        self._playwright = None
        self._browser = None
        
        if enable_js_rendering:
            try:
                from playwright.sync_api import sync_playwright
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.firefox.launch(headless=True)
                self.logger.info("Playwright initialized for JS rendering")
            except ImportError:
                self.logger.warning(
                    "Playwright not installed. Install with: pip install playwright && playwright install firefox"
                )
                self.enable_js_rendering = False
    
    def _is_js_heavy(self, html: str) -> bool:
        """
        Detect if page is JavaScript-heavy.
        
        Args:
            html: Page HTML content
            
        Returns:
            True if JS-heavy page detected
        """
        # Heuristics for JS-heavy pages
        indicators = [
            # React/Vue/Angular apps
            r'<div[^>]*id="(root|app|__next)"[^>]*></div>',
            r'<noscript>.*JavaScript.*</noscript>',
            
            # Very little body content
            len(html) < 1000 and '<script' in html,
            
            # Heavy script tags
            html.count('<script') > 10,
            
            # Common SPA frameworks
            'React' in html or 'Vue' in html or 'Angular' in html,
            
            # Loading indicators
            'loading' in html.lower() and len(re.findall(r'<[^>]*>', html)) < 20,
        ]
        
        return sum(1 for ind in indicators if ind) >= 2
    
    def get_with_js(
        self,
        url: str,
        wait_until: str = "networkidle",
        timeout: int = 30000,
        **kwargs
    ):
        """
        Fetch URL with JavaScript rendering.
        
        Args:
            url: URL to fetch
            wait_until: When to consider page loaded (networkidle, load, domcontentloaded)
            timeout: Page load timeout in milliseconds
            **kwargs: Additional arguments
            
        Returns:
            HTML content as string
        """
        if not self.enable_js_rendering or not self._browser:
            self.logger.warning("JS rendering not available, using standard GET")
            response = self.get(url, **kwargs)
            return response.text if response else ""
        
        try:
            # Rate limiting
            domain = self._get_domain(url)
            self._rate_limit(domain)
            
            self.logger.debug(f"Rendering with Playwright: {url}")
            
            page = self._browser.new_page()
            page.goto(url, wait_until=wait_until, timeout=timeout)
            
            # Wait for dynamic content
            page.wait_for_timeout(2000)  # 2 second buffer
            
            html = page.content()
            page.close()
            
            return html
            
        except Exception as e:
            self.logger.error(f"Playwright rendering failed for {url}: {e}")
            return ""
    
    def get_smart(
        self,
        url: str,
        force_js: bool = False,
        **kwargs
    ):
        """
        Smart fetch that auto-detects if JS rendering is needed.
        
        Args:
            url: URL to fetch
            force_js: Force JavaScript rendering
            **kwargs: Additional arguments
            
        Returns:
            HTML content or Response object
        """
        # Force JS if requested
        if force_js and self.enable_js_rendering:
            return self.get_with_js(url, **kwargs)
        
        # Try standard GET first
        response = self.get_safe(url, **kwargs)
        
        if not response:
            return None
        
        html = response.text
        
        # Check if JS rendering needed
        if self.enable_js_rendering and self._is_js_heavy(html):
            self.logger.info(f"JS-heavy page detected, re-fetching with Playwright: {url}")
            return self.get_with_js(url, **kwargs)
        
        return response
    
    def close(self):
        """Close browser and cleanup."""
        super().close()
        
        if self._browser:
            self._browser.close()
            self.logger.debug("Browser closed")
        
        if self._playwright:
            self._playwright.stop()
            self.logger.debug("Playwright stopped")
