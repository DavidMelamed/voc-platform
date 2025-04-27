"""
Apify Scraper for the Voice-of-Customer & Brand-Intel Platform.

This module implements the Apify Scraper which uses the Apify API
for running web scraping actors and workflows.
"""

import os
import json
import logging
import aiohttp
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .base_scraper import Scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApifyScraper(Scraper):
    """Apify-based scraper for advanced web scraping with actors."""
    
    def __init__(self):
        """Initialize the Apify scraper."""
        self.api_key = os.getenv("APIFY_API_KEY", "")
        self.api_url = "https://api.apify.com/v2"
        self.max_poll_attempts = int(os.getenv("APIFY_MAX_POLL_ATTEMPTS", "20"))
        self.poll_interval = int(os.getenv("APIFY_POLL_INTERVAL", "5"))
        
        # Map of tasks to Apify actor IDs or task IDs
        self.actor_map = {
            "webscraper": os.getenv("APIFY_WEBSCRAPER_ACTOR", "apify/web-scraper"),
            "cheerio": os.getenv("APIFY_CHEERIO_ACTOR", "apify/cheerio-scraper"),
            "playwright": os.getenv("APIFY_PLAYWRIGHT_ACTOR", "apify/playwright-scraper"),
            "amazon": os.getenv("APIFY_AMAZON_ACTOR", "vaclavrut/amazon-crawler"),
            "google": os.getenv("APIFY_GOOGLE_ACTOR", "apify/google-search-scraper"),
            "twitter": os.getenv("APIFY_TWITTER_ACTOR", "quacker/twitter-scraper"),
            "linkedin": os.getenv("APIFY_LINKEDIN_ACTOR", "dtrungtin/linkedin-scraper"),
            "facebook": os.getenv("APIFY_FACEBOOK_ACTOR", "dtrungtin/facebook-scraper"),
            # Add more actors as needed
        }
        
        logger.info(f"Initialized ApifyScraper with API URL: {self.api_url}")
        
    async def _call_api(self, endpoint: str, method: str = "GET", params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call the Apify API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET or POST)
            params: Query parameters for GET requests
            data: Request data for POST requests
            
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
                if method.upper() == "GET":
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Error calling Apify API {endpoint}: {response.status} - {error_text}")
                            raise Exception(f"Apify API {endpoint} failed: {response.status} - {error_text}")
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Error calling Apify API {endpoint}: {response.status} - {error_text}")
                            raise Exception(f"Apify API {endpoint} failed: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling Apify API {endpoint}: {str(e)}")
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
        # This scraper is suitable for advanced website scraping, e-commerce, and structured data extraction
        if source_type in ["website", "ecommerce", "amazon", "social_media", "serp"]:
            return True
            
        # If we have a URL, check if it's a website/platform we support
        if url and self.api_key:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            if any(x in domain for x in ["amazon", "linkedin.com", "twitter.com", "facebook.com", "google.com"]):
                return True
                
            # General websites are also acceptable
            if parsed_url.scheme in ["http", "https"] and parsed_url.netloc:
                return True
                
        # Support keyword-based searches when API key is available
        if self.api_key and keywords and "google" in self.actor_map:
            return True
            
        # Not suitable when API key is missing
        if not self.api_key:
            return False
            
        # Default to False for unknown cases
        return False
        
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data using Apify actors.
        
        Args:
            url: URL to scrape
            keywords: Keywords to scrape (optional, used for SERP searches or filtering content)
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        if not url and not keywords:
            raise ValueError("Either URL or keywords are required for the ApifyScraper")
            
        if not self.api_key:
            raise ValueError("APIFY_API_KEY is not set in environment variables")
            
        options = options or {}
        actor_id = self._determine_actor_id(url, keywords, options)
        if not actor_id:
            raise ValueError(f"No suitable Apify actor found for URL: {url}")
            
        max_pages = options.get("max_pages", 10)
        wait_until = options.get("wait_until", "networkidle")
        
        logger.info(f"Scraping {'URL: ' + url if url else 'Keywords: ' + str(keywords)} with Apify actor {actor_id}")
        
        try:
            # Prepare the actor run configuration
            run_input = {}
            
            # Configure input based on the actor
            if actor_id == self.actor_map.get("google"):
                # Google search
                run_input = {
                    "queries": keywords if keywords else [url],
                    "maxPagesPerQuery": max_pages,
                    "resultsPerPage": options.get("results_per_page", 10),
                    "languageCode": options.get("language", "en"),
                    "countryCode": options.get("country", "US"),
                    "mobileResults": options.get("mobile", False)
                }
            elif actor_id == self.actor_map.get("amazon"):
                # Amazon scraper
                run_input = {
                    "startUrls": [{"url": url}],
                    "maxRequestsPerCrawl": max_pages * 10,
                    "extendOutputFunction": options.get("extend_function", "({ data }) => { return data; }"),
                    "proxy": options.get("proxy", {"useApifyProxy": True})
                }
            elif any(actor_id == self.actor_map.get(x) for x in ["webscraper", "cheerio", "playwright"]):
                # Generic website scrapers
                run_input = {
                    "startUrls": [{"url": url}],
                    "maxRequestsPerCrawl": max_pages * 10,
                    "linkSelector": options.get("link_selector", "a[href]"),
                    "waitUntil": wait_until,
                    "pseudoUrls": options.get("pseudo_urls", [{"purl": "(.*)"}]),
                    "pageFunction": options.get("page_function", "({ request, response, body, contentType, $ }) => { return { url: request.url, title: $('title').text(), }; }"),
                }
            else:
                # Social media or custom actors
                run_input = {
                    "url": url,
                    "maxItems": options.get("max_items", 100),
                    "proxy": options.get("proxy", {"useApifyProxy": True})
                }
                
                # Add search terms if available
                if keywords:
                    run_input["searchTerms"] = keywords
            
            # Start the actor run
            run_data = {
                "runInput": run_input
            }
            
            run_result = await self._call_api(f"acts/{actor_id}/runs", method="POST", data=run_data)
            run_id = run_result.get("id")
            
            if not run_id:
                raise Exception("Failed to start Apify actor run: No run ID returned")
                
            logger.info(f"Started Apify actor {actor_id} run {run_id}")
            
            # Poll for run completion with enhanced monitoring
            poll_attempts = 0
            run_completed = False
            run_status = None
            
            while poll_attempts < self.max_poll_attempts and not run_completed:
                # Wait before polling
                await asyncio.sleep(self.poll_interval)
                
                # Check run status
                run_status = await self._call_api(f"actor-runs/{run_id}")
                
                status = run_status.get("status")
                if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                    run_completed = True
                    logger.info(f"Apify actor run {run_id} completed with status: {status}")
                elif status == "RUNNING":
                    progress = run_status.get('progressPercent', 0)
                    logger.info(f"Apify actor run {run_id} is running... (Progress: {progress}%)")
                elif status == "READY":
                    logger.info(f"Apify actor run {run_id} is ready to start")
                else:
                    logger.warning(f"Apify actor run {run_id} has unknown status: {status}")
                
                poll_attempts += 1
            
            if not run_completed:
                raise Exception(f"Apify actor run timed out after {poll_attempts} attempts")
                
            if run_status.get("status") != "SUCCEEDED":
                raise Exception(f"Apify actor run failed: {run_status.get('status')}")
                
            # Get the dataset ID
            dataset_id = run_status.get("defaultDatasetId")
            if not dataset_id:
                raise Exception("No dataset ID found in the run result")
                
            # Get the dataset items
            dataset_items = await self._call_api(f"datasets/{dataset_id}/items")
            items = dataset_items.get("items", [])
            
            # Return the results
            return {
                "url": url,
                "keywords": keywords,
                "run_id": run_id,
                "actor_id": actor_id,
                "data": items,
                "stats": {
                    "requestsTotal": run_status.get("stats", {}).get("requestsTotal", 0),
                    "requestsFailed": run_status.get("stats", {}).get("requestsFailed", 0),
                    "datasetsCount": run_status.get("stats", {}).get("datasetsCount", 0),
                    "resultsCount": len(items)
                },
                "metadata": {
                    "scraper": "apify",
                    "actor_id": actor_id,
                    "max_pages": max_pages,
                    "wait_until": wait_until,
                    "keywords": keywords,
                    "timestamp": run_status.get("finishedAt"),
                    "duration_secs": run_status.get("durationSecs"),
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping with Apify: {str(e)}")
            
            # Return error information
            return {
                "url": url,
                "keywords": keywords,
                "error": str(e),
                "metadata": {
                    "scraper": "apify",
                    "actor_id": actor_id,
                    "max_pages": max_pages,
                    "wait_until": wait_until,
                    "keywords": keywords,
                    "success": False
                }
            }
    
    def _determine_actor_id(self, url: str, keywords: List[str], options: Dict[str, Any]) -> str:
        """
        Determine which Apify actor to use based on the URL and keywords.
        
        Args:
            url: URL to scrape
            keywords: Keywords to scrape
            options: Additional options for the scraper
            
        Returns:
            Actor ID to use, or empty string if no suitable actor found
        """
        # Check if actor_id is directly provided in options
        if "actor_id" in options:
            return options["actor_id"]
            
        # No URL but keywords provided, use Google Search scraper
        if not url and keywords:
            return self.actor_map.get("google", "")
            
        # If no URL provided, return empty
        if not url:
            return ""
            
        # Determine platform from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if "amazon" in domain:
            return self.actor_map.get("amazon", "")
        elif "linkedin.com" in domain:
            return self.actor_map.get("linkedin", "")
        elif "twitter.com" in domain or "x.com" in domain:
            return self.actor_map.get("twitter", "")
        elif "facebook.com" in domain:
            return self.actor_map.get("facebook", "")
        elif "google.com" in domain and "/search" in parsed_url.path:
            return self.actor_map.get("google", "")
        else:
            # Determine best general scraper based on options
            if options.get("use_cheerio", False):
                return self.actor_map.get("cheerio", "")
            elif options.get("use_playwright", True):
                return self.actor_map.get("playwright", "")
            else:
                return self.actor_map.get("webscraper", "")

# Import asyncio here to avoid circular import with the class
import asyncio
