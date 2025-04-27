/**
 * Stub implementation of the Cassandra driver for local development
 * without requiring an actual Astra DB connection
 */

class Client {
  constructor(options) {
    console.log('Using stubbed Cassandra driver - no actual DB connection will be made');
    this.options = options;
    this.keyspace = options.keyspace;
  }

  /**
   * Mock connection method
   * @returns {Promise<void>}
   */
  async connect() {
    console.log('Mock Cassandra client connected');
    return Promise.resolve();
  }

  /**
   * Mock prepare statement method
   * @param {string} query - Query to prepare
   * @returns {Promise<Object>} - Prepared statement
   */
  async prepare(query) {
    return Promise.resolve({
      query,
      prepared: true
    });
  }

  /**
   * Mock execute method
   * @param {string|Object} query - Query to execute
   * @param {Array} params - Query parameters
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Query result
   */
  async execute(query, params = [], options = {}) {
    // Log the query for debugging
    console.log(`Mock query executed: ${typeof query === 'string' ? query : 'prepared statement'}`);
    
    // Return mock results based on the query type
    if (typeof query === 'string' && query.includes('SELECT')) {
      if (query.includes('vectors')) {
        return this._mockVectorResults(params);
      } else if (query.includes('raw_docs')) {
        return this._mockRawDocsResults(params);
      } else if (query.includes('insights')) {
        return this._mockInsightsResults(params);
      } else if (query.includes('graph_edges')) {
        return this._mockGraphResults(params);
      }
    }
    
    // Default empty result
    return {
      rows: [],
      pageState: null,
      executionInfo: { achievedConsistency: 1 }
    };
  }

  /**
   * Generate mock vector search results
   * @private
   * @param {Array} params - Query parameters
   * @returns {Object} - Mock result
   */
  _mockVectorResults(params) {
    const rows = [
      {
        tenant_id: params[0] || 'default',
        doc_id: '0001',
        chunk_id: '1',
        text: 'This is a mock vector search result about customer satisfaction.',
        metadata: { source_type: 'review', rating: 4.5 }
      },
      {
        tenant_id: params[0] || 'default',
        doc_id: '0002',
        chunk_id: '1',
        text: 'Mock data showing product feedback from users.',
        metadata: { source_type: 'feedback', sentiment: 'positive' }
      }
    ];
    
    return { rows };
  }

  /**
   * Generate mock raw docs results
   * @private
   * @param {Array} params - Query parameters 
   * @returns {Object} - Mock result
   */
  _mockRawDocsResults(params) {
    const rows = [
      {
        tenant_id: params[0] || 'default',
        doc_id: '0001',
        content: 'Full content of the first document with all the details.',
        source_url: 'https://example.com/review/123',
        metadata: { source_type: 'review', timestamp: new Date().toISOString() }
      }
    ];
    
    return { rows };
  }

  /**
   * Generate mock insights results
   * @private
   * @param {Array} params - Query parameters
   * @returns {Object} - Mock result
   */
  _mockInsightsResults(params) {
    const rows = [
      {
        tenant_id: params[0] || 'default',
        insight_id: '0001',
        title: 'Users want better mobile experience',
        description: 'Analysis of feedback shows mobile app needs improvement',
        source_docs: ['0001', '0002'],
        confidence: 0.87,
        created_at: new Date().toISOString()
      }
    ];
    
    return { rows };
  }

  /**
   * Generate mock graph results
   * @private
   * @param {Array} params - Query parameters
   * @returns {Object} - Mock result
   */
  _mockGraphResults(params) {
    const rows = [
      {
        tenant_id: params[0] || 'default',
        from_id: params[1] || 'entity001',
        to_id: 'entity002',
        relation_type: params[2] || 'mentions',
        weight: 0.75,
        metadata: {}
      }
    ];
    
    return { rows };
  }

  /**
   * Mock shutdown method
   * @returns {Promise<void>}
   */
  async shutdown() {
    console.log('Mock Cassandra client shut down');
    return Promise.resolve();
  }
}

module.exports = { Client };
