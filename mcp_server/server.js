const express = require('express');
const { MCP } = require('../common/mcp_stub');
const { CassandraClient } = require('./astra/client');
const { SearchService } = require('./services/search_service');
const { GraphService } = require('./services/graph_service');
const { InsightsService } = require('./services/insights_service');
const { RawDocService } = require('./services/raw_doc_service');
const { DataForSEOService } = require('./services/dataforseo_service');

// Load configuration from environment variables
const config = {
  astraDbId: process.env.ASTRA_DB_ID,
  astraDbRegion: process.env.ASTRA_DB_REGION,
  astraDbKeyspace: process.env.ASTRA_DB_KEYSPACE,
  astraDbToken: process.env.ASTRA_DB_APPLICATION_TOKEN,
  tenantId: process.env.TENANT_ID || 'default',
  port: process.env.PORT || 3000,
};

const listInsightsSchema = {
  type: 'object',
  properties: {
    filter: {
      type: 'object',
      description: 'Optional filter criteria to narrow insights',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
    lastKey: {
      type: 'string',
      description: 'Pagination token from previous request',
    },
  },
};

// Initialize Astra DB client
const astraClient = new CassandraClient(
  config.astraDbId,
  config.astraDbRegion,
  config.astraDbKeyspace,
  config.astraDbToken
);

// Initialize services
const searchService = new SearchService(astraClient, config.tenantId);
const graphService = new GraphService(astraClient, config.tenantId);
const insightsService = new InsightsService(astraClient, config.tenantId);
const rawDocService = new RawDocService(astraClient, config.tenantId);
const dataForSEOService = new DataForSEOService(
  process.env.DATAFORSEO_API_KEY,
  process.env.DATAFORSEO_LOGIN
);

// Create Express app
const app = express();
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Create MCP server
const mcpServer = new MCP('voc-platform-server');

// Define MCP tools
const vectorSearchSchema = {
  type: 'object',
  properties: {
    query: {
      type: 'string',
      description: 'The query text to search for',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
    filter: {
      type: 'object',
      description: 'Optional filter criteria',
    },
  },
  required: ['query'],
};

mcpServer.defineTool('vector-search', {
  description: 'Search for documents using a vector embedding',
  input_schema: vectorSearchSchema,
  handler: async ({ query, limit = 10, filter = {} }) => {
    return await searchService.vectorSearch(query, limit, filter);
  },
});

const hybridSearchSchema = {
  type: 'object',
  properties: {
    query: {
      type: 'string',
      description: 'The query text to search for',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
    vectorWeight: {
      type: 'number',
      description: 'Weight for vector search (0-1)',
      default: 0.5,
    },
    filter: {
      type: 'object',
      description: 'Optional filter criteria',
    },
  },
  required: ['query'],
};

mcpServer.defineTool('hybrid-search', {
  description: 'Search for documents using both keyword and semantic similarity',
  input_schema: hybridSearchSchema,
  handler: async ({ query, limit = 10, vectorWeight = 0.5, filter = {} }) => {
    return await searchService.hybridSearch(query, limit, vectorWeight, filter);
  },
});

const keywordSearchSchema = {
  type: 'object',
  properties: {
    query: {
      type: 'string',
      description: 'The keyword query to search for',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
    filter: {
      type: 'object',
      description: 'Optional filter criteria',
    },
  },
  required: ['query'],
};

mcpServer.defineTool('keyword-search', {
  description: 'Search for documents using keyword matching',
  input_schema: keywordSearchSchema,
  handler: async ({ query, limit = 10, filter = {} }) => {
    return await searchService.keywordSearch(query, limit, filter);
  },
});

const graphQuerySchema = {
  type: 'object',
  properties: {
    fromType: {
      type: 'string',
      description: 'Entity type for the starting node',
    },
    relation: {
      type: 'string',
      description: 'Relationship type to traverse',
    },
    toType: {
      type: 'string',
      description: 'Entity type for the ending node',
    },
    fromId: {
      type: 'string',
      description: 'Optional ID of the starting node',
    },
    toId: {
      type: 'string',
      description: 'Optional ID of the ending node',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
  },
  required: ['fromType', 'relation', 'toType'],
};

mcpServer.defineTool('graph-query', {
  description: 'Query the knowledge graph to find relationships',
  input_schema: graphQuerySchema,
  handler: async ({ fromType, relation, toType, fromId, toId, limit = 10 }) => {
    return await graphService.query(fromType, relation, toType, fromId, toId, limit);
  },
});

const getRawDocSchema = {
  type: 'object',
  properties: {
    docId: {
      type: 'string',
      description: 'The document ID to retrieve',
    },
  },
  required: ['docId'],
};

mcpServer.defineTool('get-raw-doc', {
  description: 'Retrieve a raw document by ID',
  input_schema: getRawDocSchema,
  handler: async ({ docId }) => {
    return await rawDocService.getDocument(docId);
  },
});

const listRawDocsSchema = {
  type: 'object',
  properties: {
    sourceType: {
      type: 'string',
      description: 'Filter by source type',
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return',
      default: 10,
    },
    lastKey: {
      type: 'string',
      description: 'Pagination token from previous request',
    },
  },
};

mcpServer.defineTool('list-raw-docs', {
  description: 'List raw documents with optional filtering',
  input_schema: listRawDocsSchema,
  handler: async ({ sourceType, limit = 10, lastKey }) => {
    return await rawDocService.listDocuments(sourceType, limit, lastKey);
  },
});

const getInsightSchema = {
  type: 'object',
  properties: {
    insightId: {
      type: 'string',
      description: 'The insight ID to retrieve',
    },
  },
  required: ['insightId'],
};

mcpServer.defineTool('get-insight', {
  description: 'Retrieve an insight by ID',
  input_schema: getInsightSchema,
  handler: async ({ insightId }) => {
    return await insightsService.getInsight(insightId);
  },
});

// Note: The listInsightsSchema was already defined in the previous (failed) attempt,
// so the SEARCH block reflects that. We are just correcting the tool definition part.
mcpServer.defineTool('list-insights', {
  description: 'List insights with optional filtering',
  input_schema: listInsightsSchema, // Use the existing constant
  handler: async ({ filter = {}, limit = 10, lastKey }) => {
    return await insightsService.listInsights(filter, limit, lastKey);
  },
});

// Define MCP resources
mcpServer.defineResource('document', {
  description: 'A document in the system',
  uri_pattern: 'doc/{id}',
  handler: async ({ id }) => {
    return await rawDocService.getDocument(id);
  },
});

mcpServer.defineResource('insight', {
  description: 'An insight in the system',
  uri_pattern: 'insight/{id}',
  handler: async ({ id }) => {
    return await insightsService.getInsight(id);
  },
});

// DataForSEO tools
const serpGoogleOrganicSchema = {
  type: 'object',
  properties: {
    keyword: {
      type: 'string',
      description: 'Search query'
    },
    location_name: {
      type: 'string',
      description: 'Location for search',
      default: 'United States'
    },
    language_code: {
      type: 'string',
      description: 'Language code',
      default: 'en'
    },
    depth: {
      type: 'number',
      description: 'Number of results to return',
      default: 100
    }
  },
  required: ['keyword']
};

// Phantombuster tools
const phantombusterAgentRunSchema = {
  type: 'object',
  properties: {
    platform: {
      type: 'string',
      description: 'Platform to scrape (linkedin, twitter, instagram, facebook, or website)',
      enum: ['linkedin', 'twitter', 'instagram', 'facebook', 'website']
    },
    url: {
      type: 'string',
      description: 'URL to scrape'
    },
    agent_id: {
      type: 'string',
      description: 'Optional: Specific Phantombuster agent ID to use'
    },
    max_results: {
      type: 'number',
      description: 'Maximum number of results to collect',
      default: 100
    },
    keywords: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'Optional: Keywords to filter the results'
    }
  },
  required: ['url']
};

// Apify tools
const apifyWebsiteScraperSchema = {
  type: 'object',
  properties: {
    url: {
      type: 'string',
      description: 'Website URL to scrape'
    },
    max_pages: {
      type: 'number',
      description: 'Maximum number of pages to scrape',
      default: 10
    },
    actor_type: {
      type: 'string',
      description: 'Apify actor type to use',
      enum: ['cheerio', 'playwright', 'webscraper'],
      default: 'playwright'
    },
    extract_selectors: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'CSS selectors to extract content from'
    }
  },
  required: ['url']
};

const apifyGoogleSearchSchema = {
  type: 'object',
  properties: {
    keywords: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'Keywords to search for'
    },
    max_pages: {
      type: 'number',
      description: 'Maximum number of pages to scrape',
      default: 5
    },
    country: {
      type: 'string',
      description: 'Country code for search results',
      default: 'US'
    },
    language: {
      type: 'string',
      description: 'Language code for search results',
      default: 'en'
    }
  },
  required: ['keywords']
};

const apifySocialMediaSchema = {
  type: 'object',
  properties: {
    url: {
      type: 'string',
      description: 'Social media profile or page URL to scrape'
    },
    platform: {
      type: 'string',
      description: 'Social media platform',
      enum: ['linkedin', 'twitter', 'facebook', 'instagram']
    },
    max_items: {
      type: 'number',
      description: 'Maximum number of items to collect',
      default: 100
    }
  },
  required: ['url', 'platform']
};

// Crawl4AI tools
const crawl4aiScraperSchema = {
  type: 'object',
  properties: {
    url: {
      type: 'string',
      description: 'URL to crawl'
    },
    depth: {
      type: 'number',
      description: 'Crawl depth (1-5)',
      default: 2
    },
    follow_links: {
      type: 'boolean',
      description: 'Whether to follow links during crawling',
      default: true
    },
    respect_robots: {
      type: 'boolean',
      description: 'Whether to respect robots.txt',
      default: true
    },
    extract_selectors: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'CSS selectors to extract content from'
    },
    keywords: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'Keywords to filter content by'
    }
  },
  required: ['url']
};

mcpServer.defineTool('serp-google-organic-live-advanced', {
  description: 'Get Google organic search results for a keyword',
  input_schema: serpGoogleOrganicSchema,
  handler: async ({ keyword, location_name = 'United States', language_code = 'en', depth = 100 }) => {
    return await dataForSEOService.serpGoogleOrganicLiveAdvanced(keyword, location_name, language_code, depth);
  }
});

const keywordsGoogleSearchVolumeSchema = {
  type: 'object',
  properties: {
    keywords: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'Keywords to check'
    },
    location_name: {
      type: 'string',
      description: 'Location for search',
      default: 'United States'
    },
    language_code: {
      type: 'string',
      description: 'Language code',
      default: 'en'
    }
  },
  required: ['keywords']
};

mcpServer.defineTool('keywords-google-ads-search-volume', {
  description: 'Get search volume data for keywords from Google Ads',
  input_schema: keywordsGoogleSearchVolumeSchema,
  handler: async ({ keywords, location_name = 'United States', language_code = 'en' }) => {
    return await dataForSEOService.keywordsGoogleAdsSearchVolume(keywords, location_name, language_code);
  }
});

const rankedKeywordsSchema = {
  type: 'object',
  properties: {
    target: {
      type: 'string',
      description: 'Target domain'
    },
    location_name: {
      type: 'string',
      description: 'Location name',
      default: 'United States'
    },
    language_code: {
      type: 'string',
      description: 'Language code',
      default: 'en'
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results',
      default: 10
    }
  },
  required: ['target']
};

mcpServer.defineTool('datalabs_google_ranked_keywords', {
  description: 'Get keywords that a domain ranks for in Google search',
  input_schema: rankedKeywordsSchema,
  handler: async ({ target, location_name = 'United States', language_code = 'en', limit = 10 }) => {
    return await dataForSEOService.dataLabsGoogleRankedKeywords(target, location_name, language_code, limit);
  }
});

const domainRankOverviewSchema = {
  type: 'object',
  properties: {
    target: {
      type: 'string',
      description: 'Target domain'
    },
    location_name: {
      type: 'string',
      description: 'Location name',
      default: 'United States'
    },
    language_code: {
      type: 'string',
      description: 'Language code',
      default: 'en'
    }
  },
  required: ['target']
};

mcpServer.defineTool('datalabs_google_domain_rank_overview', {
  description: 'Get domain ranking overview in Google search',
  input_schema: domainRankOverviewSchema,
  handler: async ({ target, location_name = 'United States', language_code = 'en' }) => {
    return await dataForSEOService.dataLabsGoogleDomainRankOverview(target, location_name, language_code);
  }
});

const serpCompetitorsSchema = {
  type: 'object',
  properties: {
    keywords: {
      type: 'array',
      items: {
        type: 'string'
      },
      description: 'Keywords to analyze'
    },
    location_name: {
      type: 'string',
      description: 'Location name',
      default: 'United States'
    },
    language_code: {
      type: 'string',
      description: 'Language code',
      default: 'en'
    },
    limit: {
      type: 'number',
      description: 'Number of results',
      default: 10
    }
  },
  required: ['keywords']
};

mcpServer.defineTool('datalabs_google_serp_competitors', {
  description: 'Get SERP competitors for keywords',
  input_schema: serpCompetitorsSchema,
  handler: async ({ keywords, location_name = 'United States', language_code = 'en', limit = 10 }) => {
    return await dataForSEOService.dataLabsGoogleSerpCompetitors(keywords, location_name, language_code, limit);
  }
});

// Phantombuster MCP Tools
mcpServer.defineTool('run_phantombuster_agent', {
  description: 'Run a Phantombuster agent for scraping',
  input_schema: phantombusterAgentRunSchema,
  handler: async ({ url, platform, agent_id, max_results = 100, keywords = [] }) => {
    // This is a mock implementation that would be replaced with actual code
    // In a real implementation, you would create a PhantombusterService similar to DataForSEOService
    const phantombusterApiKey = process.env.PHANTOMBUSTER_API_KEY;
    if (!phantombusterApiKey) {
      throw new Error("PHANTOMBUSTER_API_KEY is not set in environment variables");
    }
    
    // Mock response for now
    return {
      success: true,
      platform,
      url,
      agent_id: agent_id || `${platform}_agent_id`,
      max_results,
      keywords,
      data: [
        { id: 1, title: "Sample result 1", url: url },
        { id: 2, title: "Sample result 2", url: `${url}/page2` }
      ],
      message: "This is a mock implementation. Replace with actual Phantombuster API calls."
    };
  }
});

// Apify MCP Tools
mcpServer.defineTool('run_apify_website_scraper', {
  description: 'Run an Apify scraper to extract data from a website',
  input_schema: apifyWebsiteScraperSchema,
  handler: async ({ url, max_pages = 10, actor_type = 'playwright', extract_selectors = [] }) => {
    // This is a mock implementation that would be replaced with actual code
    // In a real implementation, you would create an ApifyService
    const apifyApiKey = process.env.APIFY_API_KEY;
    if (!apifyApiKey) {
      throw new Error("APIFY_API_KEY is not set in environment variables");
    }
    
    // Mock response for now
    return {
      success: true,
      url,
      actor_type,
      max_pages,
      extract_selectors,
      data: [
        { title: "Sample page 1", url: url, content: "Sample content for page 1" },
        { title: "Sample page 2", url: `${url}/page2`, content: "Sample content for page 2" }
      ],
      message: "This is a mock implementation. Replace with actual Apify API calls."
    };
  }
});

mcpServer.defineTool('run_apify_google_search', {
  description: 'Run an Apify scraper to extract search results from Google',
  input_schema: apifyGoogleSearchSchema,
  handler: async ({ keywords, max_pages = 5, country = 'US', language = 'en' }) => {
    // This is a mock implementation that would be replaced with actual code
    const apifyApiKey = process.env.APIFY_API_KEY;
    if (!apifyApiKey) {
      throw new Error("APIFY_API_KEY is not set in environment variables");
    }
    
    // Mock response for now
    const results = keywords.map(keyword => ({
      keyword,
      pages: Array.from({ length: Math.min(3, max_pages) }, (_, i) => ({
        page: i + 1,
        results: Array.from({ length: 10 }, (_, j) => ({
          position: j + 1,
          title: `Result ${j+1} for "${keyword}"`,
          url: `https://example.com/result${j+1}`,
          description: `This is a sample description for result ${j+1} related to "${keyword}"`
        }))
      }))
    }));
    
    return {
      success: true,
      keywords,
      country,
      language,
      max_pages,
      data: results,
      message: "This is a mock implementation. Replace with actual Apify API calls."
    };
  }
});

mcpServer.defineTool('run_apify_social_media_scraper', {
  description: 'Run an Apify scraper to extract data from social media platforms',
  input_schema: apifySocialMediaSchema,
  handler: async ({ url, platform, max_items = 100 }) => {
    // This is a mock implementation that would be replaced with actual code
    const apifyApiKey = process.env.APIFY_API_KEY;
    if (!apifyApiKey) {
      throw new Error("APIFY_API_KEY is not set in environment variables");
    }
    
    // Mock response for now
    return {
      success: true,
      url,
      platform,
      max_items,
      data: Array.from({ length: Math.min(5, max_items) }, (_, i) => ({
        id: `post_${i+1}`,
        text: `Sample ${platform} post ${i+1}`,
        date: new Date(Date.now() - i*86400000).toISOString(),
        engagement: {
          likes: Math.floor(Math.random() * 100),
          comments: Math.floor(Math.random() * 20),
          shares: Math.floor(Math.random() * 10)
        }
      })),
      message: "This is a mock implementation. Replace with actual Apify API calls."
    };
  }
});

// Crawl4AI MCP Tools
mcpServer.defineTool('run_crawl4ai_scraper', {
  description: 'Run a Crawl4AI scraper to deeply crawl and extract data from websites',
  input_schema: crawl4aiScraperSchema,
  handler: async ({ url, depth = 2, follow_links = true, respect_robots = true, extract_selectors = [], keywords = [] }) => {
    // This is a mock implementation that would be replaced with actual code
    const crawl4aiApiKey = process.env.CRAWL4AI_API_KEY;
    if (!crawl4aiApiKey) {
      throw new Error("CRAWL4AI_API_KEY is not set in environment variables");
    }
    
    // Mock response for now
    return {
      success: true,
      url,
      depth,
      follow_links,
      respect_robots,
      extract_selectors,
      keywords,
      pages: Array.from({ length: Math.min(5, depth * 2) }, (_, i) => ({
        url: i === 0 ? url : `${url}/page${i}`,
        title: `Page ${i} - ${url.split('/').pop()}`,
        content: `Sample content for page ${i}`,
        links: Array.from({ length: 3 }, (_, j) => `${url}/link${i}_${j}`),
        extracted_data: extract_selectors.reduce((acc, selector) => {
          acc[selector] = `Content extracted with selector ${selector}`;
          return acc;
        }, {})
      })),
      message: "This is a mock implementation. Replace with actual Crawl4AI API calls."
    };
  }
});

// Register MCP middleware with Express
app.use('/mcp', mcpServer.expressMiddleware());

// Start server
const server = app.listen(config.port, () => {
  console.log(`MCP Server running on port ${config.port}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    astraClient.shutdown().then(() => {
      console.log('Database connections closed');
      process.exit(0);
    });
  });
});

module.exports = { app, server, mcpServer };
