const express = require('express');
const { MCP } = require('@modelcontextprotocol/server');
const { CassandraClient } = require('./astra/client');
const { SearchService } = require('./services/search_service');
const { GraphService } = require('./services/graph_service');
const { InsightsService } = require('./services/insights_service');
const { RawDocService } = require('./services/raw_doc_service');

// Load configuration from environment variables
const config = {
  astraDbId: process.env.ASTRA_DB_ID,
  astraDbRegion: process.env.ASTRA_DB_REGION,
  astraDbKeyspace: process.env.ASTRA_DB_KEYSPACE,
  astraDbToken: process.env.ASTRA_DB_APPLICATION_TOKEN,
  tenantId: process.env.TENANT_ID || 'default',
  port: process.env.PORT || 3000,
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
mcpServer.defineTool('vector-search', {
  description: 'Search for documents using a vector embedding',
  input_schema: {
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
  },
  handler: async ({ query, limit = 10, filter = {} }) => {
    return await searchService.vectorSearch(query, limit, filter);
  },
});

mcpServer.defineTool('hybrid-search', {
  description: 'Search for documents using both keyword and semantic similarity',
  input_schema: {
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
  },
  handler: async ({ query, limit = 10, vectorWeight = 0.5, filter = {} }) => {
    return await searchService.hybridSearch(query, limit, vectorWeight, filter);
  },
});

mcpServer.defineTool('keyword-search', {
  description: 'Search for documents using keyword matching',
  input_schema: {
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
  },
  handler: async ({ query, limit = 10, filter = {} }) => {
    return await searchService.keywordSearch(query, limit, filter);
  },
});

mcpServer.defineTool('graph-query', {
  description: 'Query the knowledge graph to find relationships',
  input_schema: {
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
  },
  handler: async ({ fromType, relation, toType, fromId, toId, limit = 10 }) => {
    return await graphService.query(fromType, relation, toType, fromId, toId, limit);
  },
});

mcpServer.defineTool('get-raw-doc', {
  description: 'Retrieve a raw document by ID',
  input_schema: {
    type: 'object',
    properties: {
      docId: {
        type: 'string',
        description: 'The document ID to retrieve',
      },
    },
    required: ['docId'],
  },
  handler: async ({ docId }) => {
    return await rawDocService.getDocument(docId);
  },
});

mcpServer.defineTool('list-raw-docs', {
  description: 'List raw documents with optional filtering',
  input_schema: {
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
  },
  handler: async ({ sourceType, limit = 10, lastKey }) => {
    return await rawDocService.listDocuments(sourceType, limit, lastKey);
  },
});

mcpServer.defineTool('get-insight', {
  description: 'Retrieve an insight by ID',
  input_schema: {
    type: 'object',
    properties: {
      insightId: {
        type: 'string',
        description: 'The insight ID to retrieve',
      },
    },
    required: ['insightId'],
  },
  handler: async ({ insightId }) => {
    return await insightsService.getInsight(insightId);
  },
});

mcpServer.defineTool('list-insights', {
  description: 'List insights with optional filtering',
  input_schema: {
    type: 'object',
    properties: {
      filter: {
        type: 'object',
        description: 'Filter criteria for insights',
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
  },
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
