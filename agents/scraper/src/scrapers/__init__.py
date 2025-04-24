"""
Scrapers package for the Voice-of-Customer & Brand-Intel Platform.

This package contains the various scraper implementations used by the
Scraper Agent to collect data from different sources.
"""

from .playwright_scraper import PlaywrightScraper
from .dataforseo_scraper import DataForSEOScraper
from .crawl4ai_scraper import Crawl4AIScraper
from .firecrawl_scraper import FirecrawlScraper
from .phantombuster_scraper import PhantombusterScraper
from .apify_scraper import ApifyScraper

__all__ = [
    'PlaywrightScraper',
    'DataForSEOScraper',
    'Crawl4AIScraper',
    'FirecrawlScraper',
    'PhantombusterScraper',
    'ApifyScraper'
]
