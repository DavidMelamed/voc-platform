"""
Base Scraper interface for the Voice-of-Customer & Brand-Intel Platform.

This module defines the base Scraper interface that all specific scraper
implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class Scraper(ABC):
    """Base Scraper interface."""
    
    @abstractmethod
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data from a source.
        
        Args:
            url: URL to scrape (optional)
            keywords: Keywords to scrape (optional)
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        pass
    
    @abstractmethod
    async def is_suitable(self, url: str = None, keywords: List[str] = None, source_type: str = None) -> bool:
        """
        Check if this scraper is suitable for the given input.
        
        Args:
            url: URL to scrape (optional)
            keywords: Keywords to scrape (optional)
            source_type: Type of source (e.g., 'website', 'serp', 'social', etc.)
            
        Returns:
            True if this scraper is suitable, False otherwise
        """
        pass
