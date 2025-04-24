# Voice-of-Customer & Brand-Intel Platform

A comprehensive SaaS platform for ingesting, enriching, and serving voice-of-customer and competitive intelligence data across multiple tenants.

## Overview

The Voice-of-Customer & Brand-Intel Platform is a modular, scalable system that helps businesses collect, analyze, and leverage customer feedback and competitive intelligence from a wide range of sources. The platform combines advanced scraping capabilities, AI-powered tagging, vector embeddings, and graph relationship mapping to provide deep insights into customer sentiment, emerging trends, and competitive positioning.

## Architecture

The platform is built around a set of autonomous agents, each responsible for specific tasks:

### Coordinator Agent
- Orchestrates the entire workflow
- Pulls prioritized jobs from Pulsar queues
- Dispatches tasks to specialized agents
- Enforces budget caps and stop conditions
- Manages human-in-the-loop approvals

### Scraper Agent
- Collects data from various sources:
  - Public websites via Playwright browser automation
  - SERP and keyword data via DataForSEO 
  - Deep site crawls
  - Review sites, social media, forums
- Standardizes output for downstream processing

### Tagger Agent
- Validates input with Pydantic models
- Chunks text for optimal processing (1000 tokens, 100 overlap)
- Generates vector embeddings
- Identifies entities, sentiment, and urgency
- Creates graph relationships between entities
- Stores data in Astra DB (vectors, raw docs, graph edges)

### Data Science Agent
- Runs in a Jupyter environment
- Proposes and executes novel analyses
- Generates visualizations and insights
- Integrates with Polars, DuckDB, and graph algorithms

### MCP Server
- Provides a unified API for interacting with the platform
- Exposes vector search, hybrid search, graph queries
- Handles authentication and authorization
- Serves as a gateway for external agents

## Data Stores

- **Astra DB** - Vector-enabled database for storing:
  - Raw documents (JSON)
  - Vector embeddings 
  - Graph relationships
  - Analysis insights

- **Astra Streaming (Pulsar)** - Persistent, priority task queues:
  - scrape.jobs - Prioritized list of scraping tasks
  - scrape.results - Results from scraping operations
  - tag.complete - Notification of completed tagging
  - analysis.jobs - Proposed analytical tasks
  - analysis.done - Completed analyses

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Terraform (for infrastructure provisioning)
- Astra DB and Astra Streaming accounts
- OpenAI API key
- DataForSEO account (optional)

### Infrastructure Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/voc-platform.git
cd voc-platform
```

2. Copy the example environment file and update with your credentials:
```bash
cp .env.example .env
# Edit .env with your specific configuration
```

3. Set up Astra DB and Streaming resources using Terraform:
```bash
cd infrastructure/terraform
cp tenant.tfvars.example tenant.tfvars
# Edit tenant.tfvars with your specific tenant settings
terraform init
terraform apply -var-file=tenant.tfvars
```

4. Build and start the Docker containers:
```bash
cd ../..
docker-compose up -d
```

## Configuring a New Tenant

To set up a new tenant on the platform:

1. Create a new tenant configuration in Terraform:
```bash
cd infrastructure/terraform
cp tenant.tfvars.example tenant-clientname.tfvars
# Edit tenant-clientname.tfvars with the new tenant settings
terraform init
terraform apply -var-file=tenant-clientname.tfvars
```

2. Create a dedicated `.env` file for the tenant:
```bash
cp .env.example .env.clientname
# Update .env.clientname with the new tenant's configuration
```

3. Start services for the new tenant:
```bash
COMPOSE_PROJECT_NAME=client-name docker-compose --env-file .env.clientname up -d
```

## Usage

### Adding New Data Sources

To add a new data source for monitoring:

1. Access the coordinator dashboard (default: http://localhost:3000/dashboard)
2. Click "Add New Source"
3. Provide the URL or keywords to monitor
4. Set scraping frequency and other parameters
5. Submit the form to add to the scraping queue

### Viewing Insights

1. Access the insights dashboard (default: http://localhost:3000/insights)
2. Filter by source type, date range, or sentiment
3. Browse generated visualizations and summaries
4. Click on specific insights to view detailed analysis

### Querying the Data

The platform provides several ways to query the collected data:

#### Vector Search
```
POST /api/search/vector
{
  "tenant_id": "your-tenant-id",
  "query": "customers complaining about shipping times",
  "limit": 10
}
```

#### Hybrid Search
```
POST /api/search/hybrid
{
  "tenant_id": "your-tenant-id",
  "query": "warranty issues",
  "keywords": ["defect", "replacement"],
  "limit": 10
}
```

#### Graph Query
```
POST /api/graph/query
{
  "tenant_id": "your-tenant-id",
  "start_entity": "your-product-name",
  "relation_type": "MENTIONED_WITH",
  "max_depth": 2
}
```

## Development

### Adding New Scraper Types

To add support for a new data source:

1. Create a new scraper class in `agents/scraper/src/scrapers/`
2. Implement the base `Scraper` interface
3. Update the scraper factory to include the new scraper type
4. Test the implementation with sample sources

### Extending Entity Extraction

To support new entity types:

1. Update the entity models in `agents/tagger/src/models.py`
2. Modify the entity extractor prompts in `agents/tagger/src/entity_extractor.py`
3. Update the graph edge creation logic if needed

## Maintenance and Monitoring

The platform includes several monitoring endpoints:

- `/health` - Overall system health
- `/metrics` - Prometheus-compatible metrics
- `/logs` - Log aggregation and filtering
- `/queues` - Queue depths and processing rates

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [Astra DB Documentation](https://docs.datastax.com/en/astra/docs/)
- [Astra Streaming Documentation](https://docs.datastax.com/en/astra-streaming/docs/)
- [DataForSEO API Documentation](https://docs.dataforseo.com/)
- [Langchain Documentation](https://python.langchain.com/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
