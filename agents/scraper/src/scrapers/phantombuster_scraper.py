"""
Phantombuster Scraper for the Voice-of-Customer & Brand-Intel Platform.

This module implements the Phantombuster Scraper which uses the Phantombuster API
for running automated web scraping agents.
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

class PhantombusterScraper(Scraper):
    """Phantombuster-based scraper for social media and web data extraction."""
    
    def __init__(self):
        """Initialize the Phantombuster scraper."""
        self.api_key = os.getenv("PHANTOMBUSTER_API_KEY", "")
        self.api_url = "https://api.phantombuster.com/api/v2"
        self.max_poll_attempts = int(os.getenv("PHANTOMBUSTER_MAX_POLL_ATTEMPTS", "20"))
        self.poll_interval = int(os.getenv("PHANTOMBUSTER_POLL_INTERVAL", "5"))
        
        # Map of platforms to Phantombuster agent IDs
        self.agent_map = {
            "linkedin": os.getenv("PHANTOMBUSTER_LINKEDIN_AGENT_ID", ""),
            "twitter": os.getenv("PHANTOMBUSTER_TWITTER_AGENT_ID", ""),
            "instagram": os.getenv("PHANTOMBUSTER_INSTAGRAM_AGENT_ID", ""),
            "facebook": os.getenv("PHANTOMBUSTER_FACEBOOK_AGENT_ID", ""),
            "website": os.getenv("PHANTOMBUSTER_WEBSITE_AGENT_ID", ""),
            # Add more platforms as needed
        }
        
        logger.info(f"Initialized PhantombusterScraper with API URL: {self.api_url}")
        
    async def _call_api(self, endpoint: str, method: str = "GET", params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call the Phantombuster API.
        
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
                "X-Phantombuster-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            try:
                if method.upper() == "GET":
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Error calling Phantombuster API {endpoint}: {response.status} - {error_text}")
                            raise Exception(f"Phantombuster API {endpoint} failed: {response.status} - {error_text}")
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Error calling Phantombuster API {endpoint}: {response.status} - {error_text}")
                            raise Exception(f"Phantombuster API {endpoint} failed: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling Phantombuster API {endpoint}: {str(e)}")
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
        # This scraper is suitable for social media platforms and specific websites
        if source_type in ["social_media", "linkedin", "twitter", "instagram", "facebook"]:
            return True
            
        # If we have a URL, check if it's a supported social platform
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            if "linkedin.com" in domain or "twitter.com" in domain or "x.com" in domain or "instagram.com" in domain or "facebook.com" in domain:
                return True
                
        # Not suitable for keyword-only searches or when API key is missing
        if not self.api_key or (not url and keywords):
            return False
            
        # Default to False for unknown cases
        return False
        
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data using Phantombuster agents.
        
        Args:
            url: URL to scrape
            keywords: Keywords to scrape (optional, used for filtering content)
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        if not url:
            raise ValueError("URL is required for the PhantombusterScraper")
            
        if not self.api_key:
            raise ValueError("PHANTOMBUSTER_API_KEY is not set or invalid")
            
        options = options or {}
        agent_id = self._determine_agent_id(url, options)
        if not agent_id:
            raise ValueError(f"No suitable Phantombuster agent found for URL: {url}")
            
        max_results = options.get("max_results", 100)
        
        logger.info(f"Scraping URL: {url} with Phantombuster agent {agent_id}")
        
        try:
            # Prepare the agent launch configuration
            launch_data = {
                "id": agent_id,
                "argument": {
                    "url": url,
                    "maxResults": max_results
                }
            }
            
            # Add keywords if provided
            if keywords:
                launch_data["argument"]["keywords"] = keywords
                
            # Launch the agent
            launch_result = await self._call_api("agent/launch", method="POST", data=launch_data)
            container_id = launch_result.get("containerId")
            
            if not container_id:
                raise Exception("Failed to launch Phantombuster agent: No container ID returned")
                
            logger.info(f"Launched Phantombuster agent {agent_id} in container {container_id}")
            
            # Poll for job completion
            poll_attempts = 0
            job_completed = False
            status_result = None
            
            while poll_attempts < self.max_poll_attempts and not job_completed:
                # Wait before polling
                await asyncio.sleep(self.poll_interval)
                
                # Check container status
                status_result = await self._call_api(f"agent/output", method="GET", params={"id": agent_id, "containerId": container_id})
                
                status = status_result.get("status")
                if status in ["finished", "failed"]:
                    job_completed = True
                elif status == "launching":
                    logger.info(f"Phantombuster agent {agent_id} is launching...")
                elif status == "running":
                    logger.info(f"Phantombuster agent {agent_id} is running...")
                
                poll_attempts += 1
            
            if not job_completed:
                raise Exception(f"Phantombuster agent timed out after {poll_attempts} attempts")
                
            if status_result.get("status") == "failed":
                raise Exception(f"Phantombuster agent failed: {status_result.get('error', 'Unknown error')}")
                
            # Get the job results
            output_data = status_result.get("output", {})
            result_url = output_data.get("resultUrl")
            
            result_data = {}
            if result_url:
                # Fetch the result data from the URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_url) as response:
                        if response.status == 200:
                            try:
                                result_data = await response.json()
                            except:
                                # If not JSON, try to get raw text
                                result_data = {"raw_text": await response.text()}
            
            # Return the results
            return {
                "url": url,
                "container_id": container_id,
                "agent_id": agent_id,
                "data": result_data,
                "logs": output_data.get("logs", []),
                "metadata": {
                    "scraper": "phantombuster",
                    "agent_id": agent_id,
                    "max_results": max_results,
                    "keywords": keywords,
                    "timestamp": output_data.get("endTime"),
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
                    "scraper": "phantombuster",
                    "agent_id": agent_id,
                    "max_results": max_results,
                    "keywords": keywords,
                    "success": False
                }
            }
    
    def _determine_agent_id(self, url: str, options: Dict[str, Any]) -> str:
        """
        Determine which Phantombuster agent to use based on the URL.
        
        Args:
            url: URL to scrape
            options: Additional options for the scraper
            
        Returns:
            Agent ID to use, or empty string if no suitable agent found
        """
        # Check if agent_id is directly provided in options
        if "agent_id" in options:
            return options["agent_id"]
            
        # Determine platform from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if "linkedin.com" in domain:
            return self.agent_map.get("linkedin", "")
        elif "twitter.com" in domain or "x.com" in domain:
            return self.agent_map.get("twitter", "")
        elif "instagram.com" in domain:
            return self.agent_map.get("instagram", "")
        elif "facebook.com" in domain:
            return self.agent_map.get("facebook", "")
        else:
            # Generic website scraper
            return self.agent_map.get("website", "")

# Import asyncio here to avoid circular import with the class
import asyncio
