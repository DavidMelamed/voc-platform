const { OpenAIEmbeddings } = require('../../common/openai_stub');

/**
 * Service for performing searches against the vector database
 */
class SearchService {
  /**
   * Create a new SearchService
   * @param {CassandraClient} client - Astra DB client
   * @param {string} tenantId - Tenant ID for data partitioning
   */
  constructor(client, tenantId) {
    this.client = client;
    this.tenantId = tenantId;
    this.embeddings = new OpenAIEmbeddings();
  }

  /**
   * Search for documents using vector similarity
   * @param {string} query - Query text
   * @param {number} limit - Maximum number of results
   * @param {Object} filter - Filter criteria
   * @returns {Promise<Array>} - Search results
   */
  async vectorSearch(query, limit = 10, filter = {}) {
    try {
      // Generate embedding for the query
      const embedding = await this.embeddings.embedQuery(query);
      
      // Build filter query part if needed
      let filterQuery = '';
      const params = [this.tenantId, embedding, limit];
      
      if (filter.sourceType) {
        filterQuery = ' AND metadata[\'source_type\'] = ?';
        params.push(filter.sourceType);
      }
      
      // Execute vector search
      const query = `
        SELECT * FROM ${this.client.keyspace}.vectors 
        WHERE tenant_id = ? ${filterQuery}
        ORDER BY embedding ANN OF ? 
        LIMIT ?
      `;
      
      const result = await this.client.execute(query, params);
      
      return result.rows.map(row => this._formatSearchResult(row));
    } catch (error) {
      console.error('Vector search error:', error);
      throw error;
    }
  }

  /**
   * Search for documents using keyword matching
   * @param {string} query - Keyword query
   * @param {number} limit - Maximum number of results
   * @param {Object} filter - Filter criteria
   * @returns {Promise<Array>} - Search results
   */
  async keywordSearch(query, limit = 10, filter = {}) {
    try {
      // Clean and prepare query for full-text search
      const processedQuery = this._processKeywordQuery(query);
      
      // Build query
      let searchQuery = `
        SELECT * FROM ${this.client.keyspace}.vectors 
        WHERE tenant_id = ? AND text LIKE ? 
      `;
      
      const params = [this.tenantId, `%${processedQuery}%`];
      
      if (filter.sourceType) {
        searchQuery += ' AND metadata[\'source_type\'] = ?';
        params.push(filter.sourceType);
      }
      
      searchQuery += ' LIMIT ?';
      params.push(limit);
      
      const result = await this.client.execute(searchQuery, params);
      
      return result.rows.map(row => this._formatSearchResult(row));
    } catch (error) {
      console.error('Keyword search error:', error);
      throw error;
    }
  }

  /**
   * Search using both keyword and vector similarity
   * @param {string} query - Query text
   * @param {number} limit - Maximum number of results
   * @param {number} vectorWeight - Weight for vector results (0-1)
   * @param {Object} filter - Filter criteria
   * @returns {Promise<Array>} - Search results
   */
  async hybridSearch(query, limit = 10, vectorWeight = 0.5, filter = {}) {
    try {
      // Execute both search types
      const vectorResults = await this.vectorSearch(query, limit * 2, filter);
      const keywordResults = await this.keywordSearch(query, limit * 2, filter);
      
      // Combine and re-rank results
      const combinedResults = this._combineSearchResults(
        vectorResults, 
        keywordResults, 
        vectorWeight
      );
      
      // Return top results
      return combinedResults.slice(0, limit);
    } catch (error) {
      console.error('Hybrid search error:', error);
      throw error;
    }
  }

  /**
   * Process keyword query for better matching
   * @private
   * @param {string} query - Raw query
   * @returns {string} - Processed query
   */
  _processKeywordQuery(query) {
    // Remove special characters and normalize
    return query.replace(/[^\w\s]/gi, '')
      .toLowerCase()
      .trim();
  }

  /**
   * Combine and rank results from vector and keyword searches
   * @private
   * @param {Array} vectorResults - Vector search results
   * @param {Array} keywordResults - Keyword search results
   * @param {number} vectorWeight - Weight for vector results (0-1)
   * @returns {Array} - Combined and ranked results
   */
  _combineSearchResults(vectorResults, keywordResults, vectorWeight) {
    const keywordWeight = 1 - vectorWeight;
    const resultMap = new Map();
    
    // Process vector results
    vectorResults.forEach((result, index) => {
      const score = this._calculateScore(index, vectorResults.length, vectorWeight);
      resultMap.set(result.id + result.chunkId, {
        ...result,
        score,
      });
    });
    
    // Process keyword results and combine scores
    keywordResults.forEach((result, index) => {
      const keywordScore = this._calculateScore(index, keywordResults.length, keywordWeight);
      const key = result.id + result.chunkId;
      
      if (resultMap.has(key)) {
        // Combine scores for results found in both searches
        const existingResult = resultMap.get(key);
        resultMap.set(key, {
          ...existingResult,
          score: existingResult.score + keywordScore,
        });
      } else {
        // Add new result
        resultMap.set(key, {
          ...result,
          score: keywordScore,
        });
      }
    });
    
    // Convert to array and sort by score
    return Array.from(resultMap.values())
      .sort((a, b) => b.score - a.score);
  }

  /**
   * Calculate score based on position and weight
   * @private
   * @param {number} position - Position in results list
   * @param {number} totalResults - Total number of results
   * @param {number} weight - Weight factor
   * @returns {number} - Calculated score
   */
  _calculateScore(position, totalResults, weight) {
    // Higher positions get higher scores, scaled by weight
    return (1 - (position / totalResults)) * weight;
  }

  /**
   * Format search result
   * @private
   * @param {Object} row - Database row
   * @returns {Object} - Formatted result
   */
  _formatSearchResult(row) {
    return {
      id: row.doc_id.toString(),
      chunkId: row.chunk_id.toString(),
      text: row.text,
      metadata: row.metadata || {},
    };
  }
}

module.exports = { SearchService };
