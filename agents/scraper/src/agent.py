"""
Scraper Agent for Voice-of-Customer & Brand-Intel Platform.

This agent is responsible for scraping various data sources:
- Uses Playwright browser tool for JavaScript-heavy sites
- Leverages DataForSEO MCP endpoints for SERP/keyword data
- Utilizes Crawl4AI for deep site crawls
- Uses Firecrawl for single-URL scraping
- Can use Phantombuster or Apify when login or anti-bot measures are needed
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
from langchain_openai import ChatOpenAI

from pulsar_client import PulsarClient
from mcp_tools import MCP_TOOLS
from scrapers import (
    PlaywrightScraper, 
    DataForSEOScraper, 
    Crawl4AIScraper, 
    FirecrawlScraper,
    PhantombusterScraper,
    ApifyScraper
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Pulsar client
pulsar_client = PulsarClient()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")

class ScraperAgent:
    """Main agent class for orchestrating web scraping operations."""
    
    def __init__(self):
        """Initialize the scraper agent."""
        self.tenant_id = os.getenv("TENANT_ID", "default")
        
        # Initialize scrapers
        self.scrapers = {
            "playwright": PlaywrightScraper(),
            "dataforseo": DataForSEOScraper(),
            "crawl4ai": Crawl4AIScraper(),
            "firecrawl": FirecrawlScraper(),
            "phantombuster": PhantombusterScraper(),
            "apify": ApifyScraper()
        }
        
        # Create the CrewAI agents
        self.setup_agents()
        
        logger.info(f"Initialized ScraperAgent for tenant {self.tenant_id}")
        
    def setup_agents(self):
        """Create the CrewAI agents for different scraping tasks."""
        
        # Web browser agent
        self.browser_agent = Agent(
            role="Web Scraping Specialist",
            goal="Extract clean, structured data from websites using browser automation",
            backstory="""You are an expert in web scraping and browser automation. 
            You can navigate complex websites, handle JavaScript, and extract structured data 
            even from the most challenging sites. You know how to avoid detection and work 
            around anti-bot measures.""",
            verbose=True,
            allow_delegation=False,
            tools=MCP_TOOLS["playwright"],
            llm=llm
        )
        
        # SERP data agent
        self.serp_agent = Agent(
            role="SERP Data Analyst",
            goal="Extract valuable data from search engine results pages",
            backstory="""You are a specialist in analyzing search engine results. 
            You know how to extract SERP features, organic results, ads, and other 
            valuable data from Google and other search engines. You understand search 
            intent and can map keywords to relevant business outcomes.""",
            verbose=True,
            allow_delegation=False,
            tools=MCP_TOOLS["dataforseo"],
            llm=llm
        )
        
        # Deep crawler agent
        self.crawler_agent = Agent(
            role="Deep Web Crawler",
            goal="Systematically crawl websites to discover and extract all relevant content",
            backstory="""You are a methodical web crawler who can discover and 
            map entire websites. You know how to follow links, respect robots.txt, 
            and extract content from every page while maintaining the site structure 
            and relationships between pages.""",
            verbose=True,
            allow_delegation=False,
            tools=MCP_TOOLS["crawl4ai"] + MCP_TOOLS["firecrawl"],
            llm=llm
        )
        
        # Authentication specialist
        self.auth_agent = Agent(
            role="Authentication Specialist",
            goal="Access and extract data from sites requiring login or bypassing anti-bot measures",
            backstory="""You are a specialized scraper who can handle the most 
            challenging websites that require authentication or have sophisticated 
            anti-bot measures. You know when and how to use services like Phantombuster 
            and Apify to access restricted content ethically.""",
            verbose=True,
            allow_delegation=False,
            tools=MCP_TOOLS["phantombuster"] + MCP_TOOLS["apify"],
            llm=llm
        )
        
        # Coordinator agent
        self.coordinator_agent = Agent(
            role="Scraping Coordinator",
            goal="Determine the best approach for each scraping job and delegate accordingly",
            backstory="""You are the orchestrator of scraping operations. You analyze 
            each scraping task, determine which approach will be most effective, and 
            delegate to the appropriate specialist. You know how to combine results from 
            different sources into cohesive, structured data.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
        
    def create_scraping_task(self, job_data):
        """Create a task for the scraping job."""
        
        source_type = job_data.get("source_type", "unknown")
        url = job_data.get("url", "")
        keywords = job_data.get("keywords", [])
        
        task_description = f"""
        Extract structured data from the following source:
        
        Source type: {source_type}
        {"URL: " + url if url else ""}
        {"Keywords: " + ", ".join(keywords) if keywords else ""}
        
        Your job is to:
        1. Determine the best approach for this scraping task
        2. Execute the appropriate scraping method
        3. Extract clean, structured data
        4. Format the results in a consistent JSON structure
        
        The output should include:
        - Extracted content
        - Metadata about the source
        - Scraping timestamp
        - Success/failure status
        """
        
        task = Task(
            description=task_description,
            expected_output="Structured JSON with extracted data and metadata",
            agent=self.coordinator_agent
        )
        
        return task
        
    async def process_job(self, job_data):
        """Process a scraping job."""
        try:
            job_id = job_data.get("job_id", "unknown")
            logger.info(f"Processing scraping job: {job_id}")
            
            # Create the task
            task = self.create_scraping_task(job_data)
            
            # Create the crew
            crew = Crew(
                agents=[
                    self.coordinator_agent, 
                    self.browser_agent,
                    self.serp_agent,
                    self.crawler_agent,
                    self.auth_agent
                ],
                tasks=[task],
                verbose=True,
                process=Process.sequential
            )
            
            # Execute the crew
            result = crew.kickoff()
            
            # Process the result
            if isinstance(result, TaskOutput):
                result_text = result.raw_output
            else:
                result_text = str(result)
                
            # Try to parse the result as JSON
            try:
                structured_result = json.loads(result_text)
            except json.JSONDecodeError:
                # If not valid JSON, create a structured result
                structured_result = {
                    "content": result_text,
                    "is_raw_text": True
                }
                
            # Add job metadata
            result_data = {
                "job_id": job_id,
                "tenant_id": self.tenant_id,
                "source_type": job_data.get("source_type", "unknown"),
                "url": job_data.get("url", ""),
                "keywords": job_data.get("keywords", []),
                "result": structured_result,
                "metadata": {
                    "scrape_time": datetime.now().isoformat(),
                    "success": True
                },
                "status": "completed"
            }
            
            # Send result back to the queue
            await pulsar_client.send_message(
                "scrape.results", 
                json.dumps(result_data).encode("utf-8")
            )
            
            logger.info(f"Completed scraping job: {job_id}")
            return result_data
            
        except Exception as e:
            logger.error(f"Error processing job: {str(e)}")
            
            # Create error result
            error_data = {
                "job_id": job_data.get("job_id", "unknown"),
                "tenant_id": self.tenant_id,
                "source_type": job_data.get("source_type", "unknown"),
                "url": job_data.get("url", ""),
                "keywords": job_data.get("keywords", []),
                "error": str(e),
                "metadata": {
                    "scrape_time": datetime.now().isoformat(),
                    "success": False
                },
                "status": "error"
            }
            
            # Send error result back to the queue
            await pulsar_client.send_message(
                "scrape.results", 
                json.dumps(error_data).encode("utf-8")
            )
            
            return error_data
            
    async def start(self):
        """Start the scraper agent service."""
        logger.info("Starting Scraper Agent service")
        
        # Connect to Pulsar
        await pulsar_client.connect()
        
        # Create consumer
        await pulsar_client.create_consumer("scrape.jobs", "scraper-consumer")
        
        # Main processing loop
        try:
            while True:
                # Get next job
                message = await pulsar_client.receive_message("scrape.jobs")
                
                if message:
                    # Parse job data
                    job_data = json.loads(message.data().decode("utf-8"))
                    
                    # Process the job
                    await self.process_job(job_data)
                    
                    # Acknowledge the message
                    await pulsar_client.acknowledge(message)
                else:
                    # No jobs available, sleep before checking again
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Stopping Scraper Agent service")
        finally:
            # Close Pulsar connection
            await pulsar_client.close()
            
if __name__ == "__main__":
    # Create and start the scraper agent
    scraper = ScraperAgent()
    asyncio.run(scraper.start())
