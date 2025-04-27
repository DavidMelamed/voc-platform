#!/usr/bin/env python3
'''
Scraper Tools Validator

This script checks the configuration and connectivity for:
- Playwright
- Apify
- Phantombuster
- Crawl4AI
'''

import os
import json
import requests
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test results
results = {
    "playwright": {
        "status": "Not Tested",
        "details": ""
    },
    "apify": {
        "status": "Not Tested",
        "details": ""
    },
    "phantombuster": {
        "status": "Not Tested",
        "details": ""
    },
    "crawl4ai": {
        "status": "Not Tested",
        "details": ""
    }
}

def validate_playwright():
    '''
    Validate Playwright configuration and installation
    '''
    print("\n==== Validating Playwright Configuration ====")
    
    # Check environment variables
    browser_type = os.getenv("PLAYWRIGHT_BROWSER_TYPE", "chromium")
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true")
    
    print(f"Browser Type: {browser_type}")
    print(f"Headless Mode: {headless}")
    
    # Try to check if playwright is installed
    try:
        # Check if playwright is importable
        playwright_installed = False
        try:
            import playwright
            playwright_installed = True
            print("u2705 Playwright is installed")
        except ImportError:
            print("u26a0ufe0f Playwright is not installed in this environment")
            
        # Check for browsers using playwright CLI if installed
        if playwright_installed:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    print("u2705 Successfully initialized Playwright")
                    # Try to launch browser
                    browser_fn = getattr(p, browser_type.lower(), None)
                    if browser_fn:
                        browser = browser_fn.launch(headless=(headless.lower() == 'true'))
                        browser.close()
                        print(f"u2705 Successfully launched {browser_type} browser")
                        results["playwright"]["status"] = "Success"
                        results["playwright"]["details"] = f"Successfully launched {browser_type} browser"
                    else:
                        print(f"u274c Invalid browser type: {browser_type}")
                        results["playwright"]["status"] = "Failed"
                        results["playwright"]["details"] = f"Invalid browser type: {browser_type}"
            except Exception as e:
                print(f"u274c Error initializing Playwright: {str(e)}")
                results["playwright"]["status"] = "Failed"
                results["playwright"]["details"] = f"Error: {str(e)}"
        else:
            # Set status to warning if playwright isn't installed in this environment
            # It could still be available in the Docker container
            results["playwright"]["status"] = "Warning"
            results["playwright"]["details"] = "Not installed in current environment, but may be available in Docker"
                
    except Exception as e:
        print(f"u274c Error validating Playwright: {str(e)}")
        results["playwright"]["status"] = "Failed"
        results["playwright"]["details"] = str(e)

def validate_apify():
    '''
    Validate Apify API key and connection
    '''
    print("\n==== Validating Apify Configuration ====")
    
    # Check for Apify API key
    api_key = os.getenv("APIFY_API_KEY")
    if not api_key:
        print("u274c Apify API key is missing")
        results["apify"]["status"] = "Failed"
        results["apify"]["details"] = "API key is missing"
        return
    
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    
    # Try to make a request to the Apify API
    try:
        # Get user info to validate API key
        response = requests.get(
            "https://api.apify.com/v2/user/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"u2705 Successfully connected to Apify API")
            if "username" in user_data:
                print(f"\tUsername: {user_data['username']}")
            
            results["apify"]["status"] = "Success"
            results["apify"]["details"] = "API key is valid"
        else:
            print(f"u274c Failed to connect to Apify API: {response.status_code} - {response.text}")
            results["apify"]["status"] = "Failed"
            results["apify"]["details"] = f"API request failed: {response.status_code}"
    except Exception as e:
        print(f"u274c Error validating Apify API key: {str(e)}")
        results["apify"]["status"] = "Failed"
        results["apify"]["details"] = str(e)

def validate_phantombuster():
    '''
    Validate Phantombuster API key and agent IDs
    '''
    print("\n==== Validating Phantombuster Configuration ====")
    
    # Check for Phantombuster API key
    api_key = os.getenv("PHANTOMBUSTER_API_KEY")
    if not api_key:
        print("u274c Phantombuster API key is missing")
        results["phantombuster"]["status"] = "Failed"
        results["phantombuster"]["details"] = "API key is missing"
        return
    
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    
    # Check agent IDs
    agent_ids = {
        "LinkedIn": os.getenv("PHANTOMBUSTER_LINKEDIN_AGENT_ID"),
        "Twitter": os.getenv("PHANTOMBUSTER_TWITTER_AGENT_ID"),
        "Instagram": os.getenv("PHANTOMBUSTER_INSTAGRAM_AGENT_ID"),
        "Facebook": os.getenv("PHANTOMBUSTER_FACEBOOK_AGENT_ID"),
        "Website": os.getenv("PHANTOMBUSTER_WEBSITE_AGENT_ID")
    }
    
    # Check if any agent IDs are configured
    configured_agents = [name for name, id in agent_ids.items() if id and id.strip()]
    if configured_agents:
        print(f"Configured agents: {', '.join(configured_agents)}")
    else:
        print("u26a0ufe0f No agent IDs are configured")
    
    # Try to make a request to the Phantombuster API
    try:
        # Get account info to validate API key
        response = requests.get(
            "https://api.phantombuster.com/api/v2/me",
            headers={"X-Phantombuster-Key": api_key}
        )
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"u2705 Successfully connected to Phantombuster API")
            
            results["phantombuster"]["status"] = "Success"
            results["phantombuster"]["details"] = "API key is valid"
            
            # Add warning if no agent IDs are configured
            if not configured_agents:
                results["phantombuster"]["status"] = "Warning"
                results["phantombuster"]["details"] = "API key is valid but no agent IDs are configured"
        else:
            print(f"u274c Failed to connect to Phantombuster API: {response.status_code} - {response.text}")
            results["phantombuster"]["status"] = "Failed"
            results["phantombuster"]["details"] = f"API request failed: {response.status_code}"
    except Exception as e:
        print(f"u274c Error validating Phantombuster API key: {str(e)}")
        results["phantombuster"]["status"] = "Failed"
        results["phantombuster"]["details"] = str(e)

def validate_crawl4ai():
    '''
    Validate Crawl4AI API key and connection
    '''
    print("\n==== Validating Crawl4AI Configuration ====")
    
    # Check for Crawl4AI API key
    api_key = os.getenv("CRAWL4AI_API_KEY")
    api_url = os.getenv("CRAWL4AI_API_URL", "https://api.crawl4ai.com")
    
    if not api_key:
        print("u274c Crawl4AI API key is missing")
        results["crawl4ai"]["status"] = "Failed"
        results["crawl4ai"]["details"] = "API key is missing"
        return
    
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:5] if len(api_key) > 5 else 'Empty or too short'}...")
    
    if not api_key.strip():
        print("u274c Crawl4AI API key is empty")
        results["crawl4ai"]["status"] = "Failed"
        results["crawl4ai"]["details"] = "API key is empty"
        return
    
    # Try to make a request to the Crawl4AI API
    try:
        # Validate API key with a simple endpoint
        # This is a placeholder as there may not be a specific validation endpoint
        # Adjust based on actual Crawl4AI API
        response = requests.get(
            f"{api_url}/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            print(f"u2705 Successfully connected to Crawl4AI API")
            results["crawl4ai"]["status"] = "Success"
            results["crawl4ai"]["details"] = "API key is valid"
        else:
            print(f"u274c Failed to connect to Crawl4AI API: {response.status_code} - {response.text}")
            results["crawl4ai"]["status"] = "Failed"
            results["crawl4ai"]["details"] = f"API request failed: {response.status_code}"
    except Exception as e:
        print(f"u274c Error validating Crawl4AI API key: {str(e)}")
        results["crawl4ai"]["status"] = "Failed"
        results["crawl4ai"]["details"] = str(e)

# Main execution
if __name__ == "__main__":
    print("Starting scraper tools validation...")
    
    # Validate Playwright
    validate_playwright()
    
    # Validate Apify
    validate_apify()
    
    # Validate Phantombuster
    validate_phantombuster()
    
    # Validate Crawl4AI
    validate_crawl4ai()
    
    # Print summary
    print("\n==== Validation Results Summary ====")
    print(f"Playwright: {results['playwright']['status']}")
    print(f"Apify: {results['apify']['status']}")
    print(f"Phantombuster: {results['phantombuster']['status']}")
    print(f"Crawl4AI: {results['crawl4ai']['status']}")
    
    # Output detailed JSON result
    print("\nDetailed results:")
    print(json.dumps(results, indent=2))
