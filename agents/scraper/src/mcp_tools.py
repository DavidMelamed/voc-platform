"""
MCP tools definitions for the Scraper Agent.

This module defines the MCP tools that are used by the various
scraper agents in the CrewAI setup.
"""

from langchain.tools import BaseTool, Tool
from typing import Dict, List, Any, Optional

# Define tools for the Playwright MCP server
PLAYWRIGHT_TOOLS = [
    {
        "name": "playwright_navigate",
        "description": "Navigate to a URL using the Playwright browser",
        "parameters": {
            "url": {
                "type": "string",
                "description": "The URL to navigate to"
            },
            "browserType": {
                "type": "string",
                "enum": ["chromium", "firefox", "webkit"],
                "description": "Browser type to use"
            },
            "headless": {
                "type": "boolean",
                "description": "Whether to run in headless mode"
            }
        },
        "required": ["url"]
    },
    {
        "name": "playwright_click",
        "description": "Click on an element in the browser",
        "parameters": {
            "selector": {
                "type": "string",
                "description": "CSS selector for the element to click"
            }
        },
        "required": ["selector"]
    },
    {
        "name": "playwright_fill",
        "description": "Fill a form field with text",
        "parameters": {
            "selector": {
                "type": "string",
                "description": "CSS selector for the input field"
            },
            "value": {
                "type": "string",
                "description": "Text to fill the field with"
            }
        },
        "required": ["selector", "value"]
    },
    {
        "name": "playwright_screenshot",
        "description": "Take a screenshot of the current page",
        "parameters": {
            "name": {
                "type": "string",
                "description": "Name for the screenshot"
            },
            "selector": {
                "type": "string",
                "description": "Optional CSS selector to screenshot a specific element"
            },
            "fullPage": {
                "type": "boolean",
                "description": "Whether to capture the full page"
            }
        },
        "required": ["name"]
    },
    {
        "name": "playwright_get_visible_text",
        "description": "Get the visible text content of the current page",
        "parameters": {},
        "required": []
    },
    {
        "name": "playwright_get_visible_html",
        "description": "Get the HTML content of the current page",
        "parameters": {},
        "required": []
    },
    {
        "name": "playwright_close",
        "description": "Close the browser",
        "parameters": {},
        "required": []
    }
]

# Define tools for the DataForSEO MCP server
DATAFORSEO_TOOLS = [
    {
        "name": "serp-google-organic-live-advanced",
        "description": "Get Google organic search results for a keyword",
        "parameters": {
            "location_name": {
                "type": "string",
                "description": "Location name (e.g., 'United States')"
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g., 'en')"
            },
            "keyword": {
                "type": "string",
                "description": "Keyword to search for"
            },
            "depth": {
                "type": "number",
                "description": "Number of results to return (10-700)"
            }
        },
        "required": ["location_name", "language_code", "keyword"]
    },
    {
        "name": "keywords-google-ads-search-volume",
        "description": "Get search volume data for keywords from Google Ads",
        "parameters": {
            "location_name": {
                "type": "string",
                "description": "Location name (e.g., 'United States')"
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g., 'en')"
            },
            "keywords": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Array of keywords to get search volume for"
            }
        },
        "required": ["language_code", "keywords"]
    },
    {
        "name": "onpage-content-parsing",
        "description": "Parse the content on a specified page",
        "parameters": {
            "url": {
                "type": "string",
                "description": "URL of the page to parse"
            },
            "enable_javascript": {
                "type": "boolean",
                "description": "Enable JavaScript rendering"
            }
        },
        "required": ["url"]
    },
    {
        "name": "datalabs_google_ranked_keywords",
        "description": "Get keywords a domain is ranking for",
        "parameters": {
            "target": {
                "type": "string",
                "description": "Domain to check rankings for"
            },
            "location_name": {
                "type": "string",
                "description": "Location name (e.g., 'United States')"
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g., 'en')"
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of keywords to return"
            }
        },
        "required": ["target"]
    }
]

# Define tools for Crawl4AI
CRAWL4AI_TOOLS = [
    {
        "name": "crawl_website",
        "description": "Perform a deep crawl of a website",
        "parameters": {
            "url": {
                "type": "string",
                "description": "Starting URL for the crawl"
            },
            "max_pages": {
                "type": "number",
                "description": "Maximum number of pages to crawl"
            },
            "crawl_depth": {
                "type": "number",
                "description": "Maximum depth of the crawl"
            },
            "respect_robots_txt": {
                "type": "boolean",
                "description": "Whether to respect robots.txt rules"
            }
        },
        "required": ["url"]
    }
]

# Define tools for Firecrawl
FIRECRAWL_TOOLS = [
    {
        "name": "fetch_single_page",
        "description": "Fetch and parse a single page with Firecrawl",
        "parameters": {
            "url": {
                "type": "string",
                "description": "URL to fetch"
            },
            "extract_images": {
                "type": "boolean",
                "description": "Whether to extract images"
            },
            "extract_links": {
                "type": "boolean",
                "description": "Whether to extract links"
            },
            "javascript_rendering": {
                "type": "boolean",
                "description": "Whether to render JavaScript"
            }
        },
        "required": ["url"]
    }
]

# Define tools for Phantombuster
PHANTOMBUSTER_TOOLS = [
    {
        "name": "run_phantombuster_agent",
        "description": "Run a Phantombuster agent for scraping",
        "parameters": {
            "agent_id": {
                "type": "string",
                "description": "ID of the Phantombuster agent to run"
            },
            "arguments": {
                "type": "object",
                "description": "Arguments to pass to the agent"
            },
            "max_execution_time": {
                "type": "number",
                "description": "Maximum execution time in seconds"
            }
        },
        "required": ["agent_id"]
    }
]

# Define tools for Apify
APIFY_TOOLS = [
    {
        "name": "run_apify_actor",
        "description": "Run an Apify actor for scraping",
        "parameters": {
            "actor_id": {
                "type": "string",
                "description": "ID of the Apify actor to run"
            },
            "run_input": {
                "type": "object",
                "description": "Input data for the actor run"
            },
            "wait_for_finish": {
                "type": "boolean",
                "description": "Whether to wait for the run to finish"
            }
        },
        "required": ["actor_id", "run_input"]
    }
]

# Create the tools dictionary for all scrapers
MCP_TOOLS = {
    "playwright": PLAYWRIGHT_TOOLS,
    "dataforseo": DATAFORSEO_TOOLS,
    "crawl4ai": CRAWL4AI_TOOLS,
    "firecrawl": FIRECRAWL_TOOLS,
    "phantombuster": PHANTOMBUSTER_TOOLS,
    "apify": APIFY_TOOLS
}
