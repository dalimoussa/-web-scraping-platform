"""
Centralized logging configuration.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ScraperLogger:
    """Centralized logger for the scraper application."""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(
        cls,
        name: str = "scraper",
        log_file: str = "logs/scraper.log",
        level: str = "INFO",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
    ) -> logging.Logger:
        """
        Get or create logger instance.
        
        Args:
            name: Logger name
            log_file: Path to log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Max log file size before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to also log to console
            
        Returns:
            Configured logger instance
        """
        if cls._instance is not None:
            return cls._instance
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler (optional)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        cls._instance = logger
        return logger
    
    @classmethod
    def reset(cls):
        """Reset logger instance (useful for testing)."""
        if cls._instance:
            cls._instance.handlers.clear()
            cls._instance = None


# Convenience function
def get_logger(name: str = "scraper") -> logging.Logger:
    """Get logger instance."""
    return ScraperLogger.get_logger(name)
