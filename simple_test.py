"""
A simple test script to verify the DataForSEO MCP Server connection.
This doesn't rely on the project's module structure.
"""

import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataForSEOTest:
    """A simplified version of the DataForSEOScraper just for testing."""
    
    def __init__(self):
        """Initialize the test class."""
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.default_location = os.getenv("DATAFORSEO_DEFAULT_LOCATION", "United States")
        self.default_language = os.getenv("DATAFORSEO_DEFAULT_LANGUAGE", "en")
        
        logger.info(f"Initialized DataForSEOTest with MCP server at {self.mcp_server_url}")
        
    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
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
                logger.info(f"Calling MCP tool {tool_name} with arguments: {arguments}")
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
            
    async def run_test(self):
        """Run a simple test with a keyword."""
        test_keywords = ["astra db"]
        location = self.default_location
        language = self.default_language
        depth = 10
        
        logger.info(f"Testing SERP data for keywords: {test_keywords}")
        
        try:
            results = {}
            
            for keyword in test_keywords:
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
            result = {
                "keywords": test_keywords,
                "results": results,
                "metadata": {
                    "location": location,
                    "language": language,
                    "depth": depth,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            }
            
            print("\n--- Test Result ---")
            print(json.dumps(result, indent=2))
            print("--- End Test Result ---")
            
            if result.get("metadata", {}).get("success"):
                print("\nTest completed successfully.")
            else:
                print(f"\nTest failed: {result.get('error', 'Unknown error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error during test: {str(e)}")
            print(f"\nAn error occurred during the test: {e}")
            print("Please ensure the DataForSEO MCP server is running and accessible at the configured MCP_SERVER_URL.")
            print("Also ensure the MCP server itself is correctly configured with your DataForSEO credentials.")
            return {"error": str(e), "success": False}

async def main():
    """Main entry point."""
    test = DataForSEOTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())
