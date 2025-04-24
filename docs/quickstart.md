# Voice-of-Customer Platform - Quick Start Guide

This guide will help you get started with the Voice-of-Customer & Brand-Intel Platform for a new tenant.

## 1. Prerequisites

Before you begin, make sure you have:

- An Astra DB account (free tier works for testing)
- An Astra Streaming account
- An OpenAI API key
- Docker and Docker Compose installed
- Terraform installed (optional, for automated infrastructure setup)
- Git to clone the repository

## 2. Setting Up Astra Resources

### Astra DB Setup

1. Log in to your [Astra account](https://astra.datastax.com/)
2. Create a new database:
   - **Name**: `<tenant-name>-voc-platform`
   - **Keyspace**: `voc_platform`
   - **Region**: Choose a region close to your users

3. Create an application token with "Database Administrator" role
   - Go to Settings > Token Management
   - Create a new token with the role "Database Administrator"
   - Save the token securely; you'll need it for configuration

4. Get your database ID and region from the dashboard

### Astra Streaming Setup

1. Go to the Streaming tab in your Astra portal
2. Create a new Pulsar tenant:
   - **Name**: `<tenant-id>-voc-platform`
   - **Region**: Same as your database for best performance

3. Create a namespace for your tenant:
   - **Name**: `<tenant-id>-ns`

4. Get the connection details and token from the "Connect" tab

## 3. Local Setup

### Clone the Repository

```bash
git clone https://github.com/yourusername/voc-platform.git
cd voc-platform
```

### Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your specific details:
```
# Tenant details
TENANT_ID=your-company-id
TENANT_NAME="Your Company Name"

# Astra DB details
ASTRA_DB_ID=your-db-id
ASTRA_DB_REGION=your-db-region
ASTRA_TOKEN=your-db-token
ASTRA_API_ENDPOINT=your-db-endpoint
ASTRA_KEYSPACE=voc_platform

# Astra Streaming details
ASTRA_STREAMING_TENANT=your-streaming-tenant
ASTRA_STREAMING_NAMESPACE=your-streaming-namespace
ASTRA_STREAMING_TOKEN=your-streaming-token

# OpenAI API key
OPENAI_API_KEY=your-openai-key

# Optional: DataForSEO details if using
DATAFORSEO_API_KEY=your-dataforseo-key
DATAFORSEO_LOGIN=your-dataforseo-login
```

### Option 1: Setup Using Terraform

If you're using Terraform to set up the infrastructure:

1. Navigate to the Terraform directory:
```bash
cd infrastructure/terraform
```

2. Copy and modify the example tenant variables:
```bash
cp tenant.tfvars.example tenant.tfvars
# Edit tenant.tfvars with your specific tenant settings
```

3. Initialize and apply Terraform:
```bash
terraform init
terraform apply -var-file=tenant.tfvars
```

4. Return to the project root:
```bash
cd ../..
```

### Option 2: Manual Setup

If you're setting up manually:

1. Create the necessary tables in your Astra DB keyspace:
   - `raw_docs` - For storing raw document content
   - `vectors` - For storing vector embeddings
   - `graph_edges` - For storing relationships between entities
   - `insights` - For storing generated insights

2. Create the necessary topics in your Astra Streaming namespace:
   - `scrape.jobs`
   - `scrape.results`
   - `tag.complete`
   - `analysis.jobs`
   - `analysis.done`

## 4. Start the Platform

Build and start the Docker containers:

```bash
docker-compose up -d
```

This will start:
- MCP Server (API gateway)
- Coordinator Agent
- Scraper Agent
- Tagger Agent
- Data Science environment (Jupyter)

## 5. Verify Setup

1. Check that all containers are running:
```bash
docker-compose ps
```

2. Access the MCP Server dashboard:
```
http://localhost:3000/dashboard
```

3. Check the health endpoint:
```
http://localhost:3000/health
```

## 6. Add Your First Data Source

1. Navigate to the dashboard:
```
http://localhost:3000/dashboard
```

2. Click "Add New Source"

3. Fill in the source details:
   - **URL**: The website or review site to monitor
   - **Source Type**: Website, Review Site, SERP, etc.
   - **Scrape Frequency**: How often to check for new content
   - **Priority**: Importance (1-10)

4. Click "Submit" to add to the scraping queue

## 7. View Results

The platform will automatically:
1. Scrape the data source
2. Process and tag the content
3. Create vector embeddings
4. Extract entities and relationships
5. Analyze sentiment and urgency

You can view the results in:
- **Raw Docs**: http://localhost:3000/docs
- **Insights**: http://localhost:3000/insights
- **Entity Graph**: http://localhost:3000/graph

## 8. Using the API

The platform exposes several API endpoints:

### Vector Search

```bash
curl -X POST http://localhost:3000/api/search/vector \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "query": "customers complaining about shipping delays",
    "limit": 10
  }'
```

### Hybrid Search

```bash
curl -X POST http://localhost:3000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "query": "product issues",
    "keywords": ["defect", "quality"],
    "limit": 10
  }'
```

### Graph Query

```bash
curl -X POST http://localhost:3000/api/graph/query \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "start_entity": "your-product-name",
    "relation_type": "MENTIONED_WITH",
    "max_depth": 2
  }'
```

## 9. Next Steps

- Configure additional data sources
- Set up notifications for urgent feedback
- Customize entity extraction for your industry
- Create dashboards with key metrics
- Integrate with your existing tools via the API

## 10. Troubleshooting

### Containers Not Starting

Check logs for errors:
```bash
docker-compose logs <service-name>
```

### API Connection Issues

Verify the MCP server is running:
```bash
curl http://localhost:3000/health
```

### Missing Data

Check the queue status:
```bash
curl http://localhost:3000/queues
```

## Need Help?

- Check the full documentation: `/docs`
- Visit the GitHub repository for issues and updates
- Contact support at support@voc-platform.com
