"""
Crawl4AI Scraper for the Voice-of-Customer & Brand-Intel Platform.

This module implements the Crawl4AI Scraper which uses the Crawl4AI API
for advanced web scraping.
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .base_scraper import Scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Crawl4AIScraper(Scraper):
    """Crawl4AI-based scraper for advanced web scraping."""
    
    def __init__(self):
        """Initialize the Crawl4AI scraper."""
        self.api_key = os.getenv("CRAWL4AI_API_KEY", "")
        self.api_url = os.getenv("CRAWL4AI_API_URL", "https://api.crawl4ai.com")
        self.default_depth = int(os.getenv("CRAWL4AI_DEFAULT_DEPTH", "2"))
        
        logger.info(f"Initialized Crawl4AIScraper with API URL: {self.api_url}")
        
    async def _call_api(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the Crawl4AI API.
        
        Args:
            endpoint: API endpoint to call
            payload: Data to send to the API
            
        Returns:
            API response
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error calling Crawl4AI API {endpoint}: {response.status} - {error_text}")
                        raise Exception(f"Crawl4AI API {endpoint} failed: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling Crawl4AI API {endpoint}: {str(e)}")
                raise
            
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
        # This scraper is suitable for complex website scraping with sitemaps or deep crawling
        if source_type in ["website", "ecommerce", "review_site", "deep_crawl", "sitemap"]:
            return True
            
        # If we have a URL, check if it's a website and has an API key
        if url and self.api_key:
            parsed_url = urlparse(url)
            if parsed_url.scheme in ["http", "https"] and parsed_url.netloc:
                return True
                
        # Not suitable for keyword-only searches or when API key is missing
        if not self.api_key or (not url and keywords):
            return False
            
        # Default to False for unknown cases
        return False
        
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data from a website using Crawl4AI.
        
        Args:
            url: URL to scrape
            keywords: Keywords to scrape (optional, used for filtering content)
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        if not url:
            raise ValueError("URL is required for the Crawl4AIScraper")
            
        if not self.api_key:
            raise ValueError("CRAWL4AI_API_KEY is not set in environment variables")
            
        options = options or {}
        depth = options.get("depth", self.default_depth)
        extract_selectors = options.get("extract_selectors", [])
        follow_links = options.get("follow_links", True)
        respect_robots = options.get("respect_robots", True)
        
        logger.info(f"Scraping URL: {url}")
        
        try:
            # Prepare the scraping job request
            payload = {
                "url": url,
                "depth": depth,
                "follow_links": follow_links,
                "respect_robots": respect_robots,
                "extract_selectors": extract_selectors
            }
            
            # Add keywords if provided
            if keywords:
                payload["keywords"] = keywords
                
            # Submit the scraping job
            job_result = await self._call_api("v1/jobs", payload)
            job_id = job_result.get("job_id")
            
            if not job_id:
                raise Exception("Failed to create scraping job: No job ID returned")
                
            logger.info(f"Created scraping job {job_id}")
            
            # Poll for job completion with proper timeout and delays
            max_polls = int(os.getenv("CRAWL4AI_MAX_POLL_ATTEMPTS", "30"))
            poll_interval = int(os.getenv("CRAWL4AI_POLL_INTERVAL", "5"))
            
            job_status = {}
            is_completed = False
            poll_count = 0
            
            while not is_completed and poll_count < max_polls:
                # Wait before polling
                await asyncio.sleep(poll_interval)
                
                # Check job status
                job_status = await self._call_api(f"v1/jobs/{job_id}", {})
                current_status = job_status.get("status", "")
                
                if current_status == "completed":
                    is_completed = True
                    logger.info(f"Crawl4AI job {job_id} completed successfully")
                elif current_status == "failed":
                    raise Exception(f"Crawl4AI job {job_id} failed: {job_status.get('error', 'Unknown error')}")
                elif current_status == "running" or current_status == "queued":
                    progress = job_status.get("progress", 0)
                    logger.info(f"Crawl4AI job {job_id} is {current_status}... ({progress}% complete)")
                else:
                    logger.warning(f"Crawl4AI job {job_id} has unknown status: {current_status}")
                    
                poll_count += 1
            
            if not is_completed:
                raise Exception(f"Crawl4AI job {job_id} timed out after {poll_count} polling attempts")
                
            # Get the job results
            job_results = await self._call_api(f"v1/jobs/{job_id}/results", {})
            
            # Process the results
            pages = job_results.get("pages", [])
            links = job_results.get("links", [])
            extracted_data = job_results.get("extracted_data", {})
            
            # Return the results
            return {
                "url": url,
                "job_id": job_id,
                "pages": pages,
                "links": links,
                "extracted_data": extracted_data,
                "metadata": {
                    "scraper": "crawl4ai",
                    "depth": depth,
                    "follow_links": follow_links,
                    "respect_robots": respect_robots,
                    "keywords": keywords,
                    "extract_selectors": extract_selectors,
                    "timestamp": job_results.get("timestamp"),
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            
            # Return error information
            return {
                "url": url,
                "error": str(e),
                "metadata": {
                    "scraper": "crawl4ai",
                    "depth": depth,
                    "follow_links": follow_links,
                    "respect_robots": respect_robots,
                    "keywords": keywords,
                    "extract_selectors": extract_selectors,
                    "success": False
                }
            }
