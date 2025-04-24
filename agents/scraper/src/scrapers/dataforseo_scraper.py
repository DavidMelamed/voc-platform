"""
DataForSEO Scraper for the Voice-of-Customer & Brand-Intel Platform.

This module implements the DataForSEO Scraper which uses the DataForSEO
MCP server for SERP and keyword data.
"""

import os
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_scraper import Scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataForSEOScraper(Scraper):
    """DataForSEO-based scraper for SERP and keyword data."""
    
    def __init__(self):
        """Initialize the DataForSEO scraper."""
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.default_location = os.getenv("DATAFORSEO_DEFAULT_LOCATION", "United States")
        self.default_language = os.getenv("DATAFORSEO_DEFAULT_LANGUAGE", "en")
        
        logger.info(f"Initialized DataForSEOScraper with MCP server at {self.mcp_server_url}")
        
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the DataForSEO server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool response
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.mcp_server_url}/mcp/tools/{tool_name}"
            
            try:
                async with session.post(url, json=arguments) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("result", {})
                    else:
                        error_text = await response.text()
                        logger.error(f"Error calling MCP tool {tool_name}: {response.status} - {error_text}")
                        raise Exception(f"MCP tool {tool_name} failed: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling MCP tool {tool_name}: {str(e)}")
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
        # This scraper is suitable for SERP-related scraping
        if source_type in ["serp", "keyword_research", "competitive_analysis"]:
            return True
            
        # Suitable for keyword-based searches
        if not url and keywords:
            return True
            
        # Also suitable for domain analysis
        if url and source_type in ["domain_analysis", "seo"]:
            return True
            
        # Default to False for other cases
        return False
        
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data from DataForSEO APIs.
        
        Args:
            url: URL to analyze (e.g., a domain for SEO analysis)
            keywords: Keywords to search for
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        if not url and not keywords:
            raise ValueError("Either URL or keywords are required for the DataForSEOScraper")
            
        options = options or {}
        location = options.get("location", self.default_location)
        language = options.get("language", self.default_language)
        depth = options.get("depth", 100)  # Number of results to return
        
        # Determine which API to use based on inputs
        if keywords and not url:
            # SERP data for keywords
            return await self._scrape_serp_data(keywords, location, language, depth)
        elif url and not keywords:
            # Domain analysis
            return await self._scrape_domain_data(url, location, language, depth)
        else:
            # Both URL and keywords - domain competitive analysis
            return await self._scrape_competitive_data(url, keywords, location, language, depth)
            
    async def _scrape_serp_data(self, keywords: List[str], location: str, language: str, depth: int) -> Dict[str, Any]:
        """
        Scrape SERP data for keywords.
        
        Args:
            keywords: Keywords to search for
            location: Location name
            language: Language code
            depth: Number of results to return
            
        Returns:
            Dictionary containing the scraped SERP data
        """
        logger.info(f"Scraping SERP data for keywords: {keywords}")
        
        try:
            results = {}
            
            # Process each keyword
            for keyword in keywords:
                logger.info(f"Getting SERP data for keyword: {keyword}")
                
                # Call the SERP API
                serp_data = await self._call_mcp_tool("serp-google-organic-live-advanced", {
                    "location_name": location,
                    "language_code": language,
                    "keyword": keyword,
                    "depth": depth
                })
                
                # Get keyword volume data
                volume_data = await self._call_mcp_tool("keywords-google-ads-search-volume", {
                    "location_name": location,
                    "language_code": language,
                    "keywords": [keyword]
                })
                
                # Store the combined results
                results[keyword] = {
                    "serp": serp_data,
                    "volume": volume_data.get("tasks", [{}])[0].get("result", [{}])[0] if volume_data.get("tasks") else {}
                }
                
            # Return the combined results
            return {
                "keywords": keywords,
                "results": results,
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "depth": depth,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping SERP data: {str(e)}")
            
            # Return error information
            return {
                "keywords": keywords,
                "error": str(e),
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
            }
            
    async def _scrape_domain_data(self, url: str, location: str, language: str, limit: int) -> Dict[str, Any]:
        """
        Scrape domain data for a URL.
        
        Args:
            url: Domain to analyze
            location: Location name
            language: Language code
            limit: Number of results to return
            
        Returns:
            Dictionary containing the scraped domain data
        """
        logger.info(f"Scraping domain data for URL: {url}")
        
        try:
            # Extract domain from URL
            domain = self._extract_domain(url)
            
            # Get domain ranking keywords
            ranking_data = await self._call_mcp_tool("datalabs_google_ranked_keywords", {
                "target": domain,
                "location_name": location,
                "language_code": language,
                "limit": limit
            })
            
            # Get domain rank overview
            overview_data = await self._call_mcp_tool("datalabs_google_domain_rank_overview", {
                "target": domain,
                "location_name": location,
                "language_code": language
            })
            
            # Return the combined results
            return {
                "domain": domain,
                "ranking_keywords": ranking_data.get("ranked_keywords", []),
                "rank_overview": overview_data.get("metrics", {}),
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping domain data: {str(e)}")
            
            # Return error information
            return {
                "domain": self._extract_domain(url),
                "error": str(e),
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
            }
            
    async def _scrape_competitive_data(self, url: str, keywords: List[str], location: str, language: str, limit: int) -> Dict[str, Any]:
        """
        Scrape competitive data for a domain and keywords.
        
        Args:
            url: Domain to analyze
            keywords: Keywords to analyze
            location: Location name
            language: Language code
            limit: Number of results to return
            
        Returns:
            Dictionary containing the scraped competitive data
        """
        logger.info(f"Scraping competitive data for URL {url} and keywords: {keywords}")
        
        try:
            # Extract domain from URL
            domain = self._extract_domain(url)
            
            # Get SERP competitors for the domain's keywords
            competitor_data = await self._call_mcp_tool("datalabs_google_serp_competitors", {
                "keywords": keywords,
                "location_name": location,
                "language_code": language,
                "limit": limit
            })
            
            # Return the competitive analysis results
            return {
                "domain": domain,
                "keywords": keywords,
                "competitors": competitor_data.get("competitors", []),
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping competitive data: {str(e)}")
            
            # Return error information
            return {
                "domain": self._extract_domain(url),
                "keywords": keywords,
                "error": str(e),
                "metadata": {
                    "scraper": "dataforseo",
                    "location": location,
                    "language": language,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
            }
            
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain name from a URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        if not url:
            return ""
            
        # Remove protocol
        if "://" in url:
            url = url.split("://")[1]
            
        # Remove path and query string
        if "/" in url:
            url = url.split("/")[0]
            
        # Remove subdomain (keep only the main domain)
        parts = url.split(".")
        if len(parts) > 2:
            if parts[-2] not in ["co", "com", "org", "net", "gov"]:
                return ".".join(parts[-2:])
            else:
                return ".".join(parts[-3:])
                
        return url
