"""
Base scraper class with common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

from ..core.http_client import HTTPClient
from ..core.logger import get_logger
from ..core.config import get_config


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    Provides common functionality for data collection.
    """
    
    def __init__(self, http_client: Optional[HTTPClient] = None):
        """
        Initialize base scraper.
        
        Args:
            http_client: HTTP client instance (creates new if None)
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config = get_config()
        
        if http_client is None:
            scraping_config = self.config.scraping
            http_client = HTTPClient(
                default_delay=scraping_config.get('default_delay', 1.5),
                max_retries=scraping_config.get('max_retries', 3),
                timeout=scraping_config.get('timeout', 30),
                respect_robots_txt=scraping_config.get('respect_robots_txt', True),
                use_cache=scraping_config.get('use_cache', True),
                user_agent=scraping_config.get('user_agent', 'PublicOfficialsScraper/1.0'),
            )
        
        self.http = http_client
        self.results: List[Dict[str, Any]] = []
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List of scraped records
        """
        pass
    
    def generate_id(self, *components: str) -> str:
        """
        Generate unique ID from components.
        
        Args:
            *components: Strings to hash
            
        Returns:
            Hash-based ID
        """
        combined = "|".join(str(c) for c in components if c)
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    def get_timestamp(self) -> datetime:
        """Get current timestamp."""
        return datetime.now()
    
    def log_progress(self, current: int, total: int, item: str = "items"):
        """
        Log progress.
        
        Args:
            current: Current count
            total: Total count
            item: Item name for logging
        """
        if total > 0:
            percent = (current / total) * 100
            self.logger.info(f"Progress: {current}/{total} {item} ({percent:.1f}%)")
        else:
            self.logger.info(f"Processed: {current} {item}")
    
    def add_result(self, record: Dict[str, Any]):
        """
        Add record to results.
        
        Args:
            record: Data record
        """
        self.results.append(record)
    
    def clear_results(self):
        """Clear collected results."""
        self.results = []
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get collected results."""
        return self.results
