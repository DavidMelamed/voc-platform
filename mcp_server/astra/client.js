const { Client } = require('../../common/cassandra_stub');
const { OpenAIEmbeddings } = require('../../common/openai_stub');

/**
 * Client for interacting with DataStax Astra DB
 */
class CassandraClient {
  /**
   * Create a new CassandraClient
   * @param {string} dbId - Astra DB ID
   * @param {string} region - Astra DB region
   * @param {string} keyspace - Keyspace name
   * @param {string} token - Astra DB application token
   */
  constructor(dbId, region, keyspace, token) {
    this.dbId = dbId;
    this.region = region;
    this.keyspace = keyspace;
    this.token = token;
    this.embeddings = new OpenAIEmbeddings();
    
    // Initialize Cassandra client
    this.client = new Client({
      cloud: {
        secureConnectBundle: this._getSecureBundle(),
      },
      credentials: {
        username: 'token',
        password: token,
      },
      keyspace: keyspace,
    });
    
    // Prepared statements for common operations
    this.preparedStatements = {};
  }

  /**
   * Get secure connect bundle for Astra DB
   * @private
   * @returns {Buffer} - Secure connect bundle
   */
  _getSecureBundle() {
    // In a real implementation, this would download the secure connect bundle
    // For now, we'll just return a placeholder
    return Buffer.from('secure-connect-bundle-placeholder');
  }

  /**
   * Connect to Astra DB
   * @returns {Promise<void>}
   */
  async connect() {
    await this.client.connect();
    console.log('Connected to Astra DB');
    await this._prepareStatements();
  }

  /**
   * Prepare common statements for better performance
   * @private
   * @returns {Promise<void>}
   */
  async _prepareStatements() {
    // Raw docs statements
    this.preparedStatements.getRawDoc = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.raw_docs 
       WHERE tenant_id = ? AND doc_id = ?`
    );
    
    this.preparedStatements.listRawDocs = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.raw_docs 
       WHERE tenant_id = ? AND source_type = ? LIMIT ?`
    );
    
    // Vector search statement
    this.preparedStatements.vectorSearch = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.vectors 
       WHERE tenant_id = ? 
       ORDER BY embedding ANN OF ? LIMIT ?`
    );
    
    // Graph edge statements
    this.preparedStatements.getEdges = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.graph_edges 
       WHERE tenant_id = ? AND from_id = ? AND relation_type = ?`
    );
    
    // Insights statements
    this.preparedStatements.getInsight = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.insights 
       WHERE tenant_id = ? AND insight_id = ?`
    );
    
    this.preparedStatements.listInsights = await this.client.prepare(
      `SELECT * FROM ${this.keyspace}.insights 
       WHERE tenant_id = ? LIMIT ?`
    );
  }

  /**
   * Execute a CQL query
   * @param {string} query - CQL query to execute
   * @param {Array} params - Query parameters
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Query result
   */
  async execute(query, params = [], options = {}) {
    return this.client.execute(query, params, options);
  }

  /**
   * Execute a prepared statement
   * @param {string} statementName - Name of the prepared statement
   * @param {Array} params - Statement parameters
   * @param {Object} options - Statement options
   * @returns {Promise<Object>} - Statement result
   */
  async executePrepared(statementName, params = [], options = {}) {
    if (!this.preparedStatements[statementName]) {
      throw new Error(`Prepared statement '${statementName}' not found`);
    }
    return this.client.execute(this.preparedStatements[statementName], params, options);
  }

  /**
   * Perform a vector search
   * @param {string} query - Query text
   * @param {number} limit - Maximum number of results
   * @param {Object} filter - Filter criteria
   * @returns {Promise<Array>} - Search results
   */
  async vectorSearch(query, limit = 10, filter = {}) {
    try {
      // Generate embedding for the query
      const embedding = await this.embeddings.embedQuery(query);
      
      // Execute vector search
      const result = await this.executePrepared('vectorSearch', [
        filter.tenantId || this.tenantId,
        embedding,
        limit
      ]);
      
      return result.rows.map(row => this._formatVectorResult(row));
    } catch (error) {
      console.error('Vector search error:', error);
      throw error;
    }
  }

  /**
   * Format a vector search result row
   * @private
   * @param {Object} row - Raw database row
   * @returns {Object} - Formatted result
   */
  _formatVectorResult(row) {
    return {
      id: row.doc_id.toString(),
      chunkId: row.chunk_id.toString(),
      text: row.text,
      metadata: row.metadata || {},
    };
  }

  /**
   * Shut down the client
   * @returns {Promise<void>}
   */
  async shutdown() {
    await this.client.shutdown();
    console.log('Astra DB client shut down');
  }
}

module.exports = { CassandraClient };
