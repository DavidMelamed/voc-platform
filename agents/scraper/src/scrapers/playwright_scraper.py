"""
Playwright Scraper for the Voice-of-Customer & Brand-Intel Platform.

This module implements the Playwright Scraper which uses the Playwright
MCP server for browser-based scraping.
"""

import os
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from .base_scraper import Scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaywrightScraper(Scraper):
    """Playwright-based scraper for browser automation."""
    
    def __init__(self):
        """Initialize the Playwright scraper."""
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.browser_type = os.getenv("PLAYWRIGHT_BROWSER_TYPE", "chromium")
        self.headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
        
        logger.info(f"Initialized PlaywrightScraper with MCP server at {self.mcp_server_url}")
        
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the Playwright server.
        
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
        # This scraper is suitable for website scraping
        if source_type in ["website", "review_site", "social_media"]:
            return True
            
        # If we have a URL, check if it's a website
        if url:
            parsed_url = urlparse(url)
            if parsed_url.scheme in ["http", "https"] and parsed_url.netloc:
                return True
                
        # Not suitable for keyword-only searches
        if not url and keywords:
            return False
            
        # Default to False for unknown cases
        return False
        
    async def scrape(self, url: str = None, keywords: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape data from a website using Playwright.
        
        Args:
            url: URL to scrape
            keywords: Keywords to scrape (ignored by this scraper)
            options: Additional options for the scraper
            
        Returns:
            Dictionary containing the scraped data and metadata
        """
        if not url:
            raise ValueError("URL is required for the PlaywrightScraper")
            
        options = options or {}
        wait_for_selector = options.get("wait_for_selector")
        take_screenshot = options.get("take_screenshot", True)
        extract_links = options.get("extract_links", True)
        browser_type = options.get("browser_type", self.browser_type)
        headless = options.get("headless", self.headless)
        
        logger.info(f"Scraping URL: {url}")
        
        try:
            # Navigate to the URL
            navigate_result = await self._call_mcp_tool("playwright_navigate", {
                "url": url,
                "browserType": browser_type,
                "headless": headless
            })
            
            # Wait for any specific selector if provided
            if wait_for_selector:
                await self._call_mcp_tool("playwright_wait_for_selector", {
                    "selector": wait_for_selector
                })
                
            # Take a screenshot if requested
            screenshot_data = None
            if take_screenshot:
                screenshot_result = await self._call_mcp_tool("playwright_screenshot", {
                    "name": "page_screenshot",
                    "fullPage": True
                })
                screenshot_data = screenshot_result.get("base64", None)
                
            # Get the page content
            html_content = await self._call_mcp_tool("playwright_get_visible_html", {})
            text_content = await self._call_mcp_tool("playwright_get_visible_text", {})
            
            # Extract links if requested
            links = []
            if extract_links and html_content.get("html", ""):
                # Extract all links from the page
                extract_links_result = await self._call_mcp_tool("playwright_eval", {
                    "expression": "Array.from(document.querySelectorAll('a')).map(a => {"
                        + "return {href: a.href, text: a.textContent.trim(), title: a.title || null, "
                        + "target: a.target || null, rel: a.rel || null, isExternal: a.hostname !== window.location.hostname};})"
                })
                
                # Process the extracted links
                if extract_links_result and "result" in extract_links_result:
                    raw_links = extract_links_result["result"]
                    base_domain = urlparse(url).netloc
                    
                    for link in raw_links:
                        if link.get("href"):
                            # Add the link to the list
                            links.append({
                                "url": link["href"],
                                "text": link.get("text", ""),
                                "title": link.get("title"),
                                "is_external": link.get("isExternal", False),
                                "meta": {
                                    "target": link.get("target"),
                                    "rel": link.get("rel")
                                }
                            })
                
                logger.info(f"Extracted {len(links)} links from {url}")
                
            # Close the browser
            await self._call_mcp_tool("playwright_close", {})
            
            # Return the results
            result = {
                "url": url,
                "title": self._extract_title(html_content),
                "html": html_content,
                "text": text_content,
                "links": links,
                "screenshot": screenshot_data,
                "metadata": {
                    "scraper": "playwright",
                    "browser_type": browser_type,
                    "headless": headless
                }
            }
            
            logger.info(f"Successfully scraped URL: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            
            # Try to close the browser if an error occurs
            try:
                await self._call_mcp_tool("playwright_close", {})
            except Exception:
                pass
                
            # Return error information
            return {
                "url": url,
                "error": str(e),
                "metadata": {
                    "scraper": "playwright",
                    "browser_type": browser_type,
                    "headless": headless,
                    "success": False
                }
            }
            
    def _extract_title(self, html_content: str) -> str:
        """
        Extract the title from HTML content.
        
        Args:
            html_content: HTML content to extract title from
            
        Returns:
            Extracted title or empty string if not found
        """
        if not html_content:
            return ""
            
        # Simple regex-style extraction for example purposes
        # In a real implementation, we would use a proper HTML parser
        title_start = html_content.find("<title>")
        if title_start != -1:
            title_end = html_content.find("</title>", title_start)
            if title_end != -1:
                return html_content[title_start + 7:title_end].strip()
                
        return ""
