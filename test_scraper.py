# test_scraper.py
import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add agents directory to path to allow imports
# Assuming the script is run from the project root
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

# Direct import to avoid __init__.py which tries to import non-existent modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'scraper', 'src'))
try:
    # Import base scraper first (required by dataforseo_scraper)
    base_scraper_path = os.path.join(os.path.dirname(__file__), 'agents', 'scraper', 'src', 'scrapers', 'base_scraper.py')
    scrapers_dir = os.path.join(os.path.dirname(__file__), 'agents', 'scraper', 'src', 'scrapers')
    
    # Create a spec for the base_scraper module
    import importlib.util
    base_spec = importlib.util.spec_from_file_location("base_scraper", base_scraper_path)
    base_scraper = importlib.util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_scraper)
    
    # Now import the DataForSEOScraper
    dataforseo_path = os.path.join(scrapers_dir, 'dataforseo_scraper.py')
    dataforseo_spec = importlib.util.spec_from_file_location("dataforseo_scraper", dataforseo_path)
    dataforseo_scraper = importlib.util.module_from_spec(dataforseo_spec)
    dataforseo_spec.loader.exec_module(dataforseo_scraper)
    
    # Get the DataForSEOScraper class
    DataForSEOScraper = dataforseo_scraper.DataForSEOScraper
    
except ImportError as e:
    print(f"Error importing scraper: {e}")
    print("Please ensure you are running this script from the project root directory.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error importing scraper: {e}")
    sys.exit(1)

async def run_test():
    print("Initializing DataForSEOScraper...")
    # MCP_SERVER_URL should be loaded from .env by load_dotenv()
    mcp_url = os.getenv('MCP_SERVER_URL')
    if not mcp_url:
        print("Error: MCP_SERVER_URL not found in environment variables. Make sure it's set in your .env file.")
        return

    print(f"Using MCP Server URL: {mcp_url}")
    scraper = DataForSEOScraper() # It reads MCP_SERVER_URL internally

    test_keywords = ["astra db"]
    print(f"Attempting to scrape SERP data for keywords: {test_keywords}...")

    try:
        # Call the scrape method which internally calls the MCP tool
        result = await scraper.scrape(keywords=test_keywords, source_type='serp')
        print("\n--- Scraper Result ---")
        print(json.dumps(result, indent=2))
        print("--- End Scraper Result ---")

        if result.get("metadata", {}).get("success"):
            print("\nScraping test completed successfully.")
        else:
            print(f"\nScraping test failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\nAn error occurred during the scraping test: {e}")
        print("Please ensure the DataForSEO MCP server is running and accessible at the configured MCP_SERVER_URL.")
        print("Also ensure the MCP server itself is correctly configured with your DataForSEO credentials.")

if __name__ == "__main__":
    # Check if python-dotenv is installed
    try:
        import dotenv
    except ImportError:
        print("Error: python-dotenv is not installed.")
        print("Please install it: pip install python-dotenv")
        sys.exit(1)

    asyncio.run(run_test())
