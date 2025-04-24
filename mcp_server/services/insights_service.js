const { v4: uuidv4 } = require('uuid');

/**
 * Service for managing insights and analysis results
 */
class InsightsService {
  /**
   * Create a new InsightsService
   * @param {CassandraClient} client - Astra DB client
   * @param {string} tenantId - Tenant ID for data partitioning
   */
  constructor(client, tenantId) {
    this.client = client;
    this.tenantId = tenantId;
  }

  /**
   * Get an insight by ID
   * @param {string} insightId - Insight ID
   * @returns {Promise<Object>} - Insight data
   */
  async getInsight(insightId) {
    try {
      const result = await this.client.executePrepared('getInsight', [
        this.tenantId,
        insightId
      ]);
      
      if (result.rowLength === 0) {
        throw new Error(`Insight not found: ${insightId}`);
      }
      
      return this._formatInsight(result.first());
    } catch (error) {
      console.error(`Error getting insight ${insightId}:`, error);
      throw error;
    }
  }

  /**
   * List insights with optional filtering
   * @param {Object} filter - Filter criteria
   * @param {number} limit - Maximum number of results
   * @param {string} lastKey - Pagination token
   * @returns {Promise<Object>} - List of insights with pagination info
   */
  async listInsights(filter = {}, limit = 10, lastKey = null) {
    try {
      let queryConditions = ['tenant_id = ?'];
      let queryParams = [this.tenantId];
      
      // Apply filters
      if (filter.title) {
        queryConditions.push('title LIKE ?');
        queryParams.push(`%${filter.title}%`);
      }
      
      if (filter.sourceIds) {
        queryConditions.push('source_ids CONTAINS ?');
        queryParams.push(filter.sourceIds);
      }
      
      if (filter.fromDate) {
        queryConditions.push('created_at >= ?');
        queryParams.push(new Date(filter.fromDate));
      }
      
      if (filter.toDate) {
        queryConditions.push('created_at <= ?');
        queryParams.push(new Date(filter.toDate));
      }
      
      // Add pagination if last key provided
      if (lastKey) {
        queryConditions.push('token(insight_id) > token(?)');
        queryParams.push(lastKey);
      }
      
      // Build query
      const queryString = `
        SELECT * FROM ${this.client.keyspace}.insights 
        WHERE ${queryConditions.join(' AND ')} 
        LIMIT ?
      `;
      queryParams.push(limit);
      
      const result = await this.client.execute(queryString, queryParams);
      
      // Get the last insight ID for pagination
      let nextPageToken = null;
      if (result.rows.length === limit) {
        nextPageToken = result.rows[result.rows.length - 1].insight_id.toString();
      }
      
      return {
        insights: result.rows.map(row => this._formatInsight(row)),
        pagination: {
          nextPageToken,
          count: result.rows.length
        }
      };
    } catch (error) {
      console.error('Error listing insights:', error);
      throw error;
    }
  }

  /**
   * Create a new insight
   * @param {string} title - Insight title
   * @param {string} description - Insight description
   * @param {Array<string>} sourceIds - IDs of source documents
   * @param {Array<string>} artifactUrls - URLs to artifacts (e.g., charts, notebooks)
   * @param {Object} metadata - Additional metadata
   * @returns {Promise<Object>} - Created insight
   */
  async createInsight(title, description, sourceIds = [], artifactUrls = [], metadata = {}) {
    try {
      const insightId = uuidv4();
      const now = new Date();
      
      const query = `
        INSERT INTO ${this.client.keyspace}.insights (
          tenant_id, insight_id, title, description, source_ids,
          created_at, artifact_urls, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `;
      
      await this.client.execute(query, [
        this.tenantId,
        insightId,
        title,
        description,
        sourceIds,
        now,
        artifactUrls,
        metadata
      ]);
      
      return {
        id: insightId,
        tenantId: this.tenantId,
        title,
        description,
        sourceIds,
        createdAt: now,
        artifactUrls,
        metadata
      };
    } catch (error) {
      console.error('Error creating insight:', error);
      throw error;
    }
  }

  /**
   * Update an existing insight
   * @param {string} insightId - Insight ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} - Updated insight
   */
  async updateInsight(insightId, updates) {
    try {
      // Get the current insight
      const current = await this.getInsight(insightId);
      
      // Prepare update fields
      const updateFields = [];
      const updateParams = [];
      
      if (updates.title !== undefined) {
        updateFields.push('title = ?');
        updateParams.push(updates.title);
      }
      
      if (updates.description !== undefined) {
        updateFields.push('description = ?');
        updateParams.push(updates.description);
      }
      
      if (updates.sourceIds !== undefined) {
        updateFields.push('source_ids = ?');
        updateParams.push(updates.sourceIds);
      }
      
      if (updates.artifactUrls !== undefined) {
        updateFields.push('artifact_urls = ?');
        updateParams.push(updates.artifactUrls);
      }
      
      if (updates.metadata !== undefined) {
        updateFields.push('metadata = ?');
        updateParams.push({
          ...current.metadata,
          ...updates.metadata
        });
      }
      
      // Add tenant_id and insight_id to params
      updateParams.push(this.tenantId, insightId);
      
      // Build and execute query
      const query = `
        UPDATE ${this.client.keyspace}.insights 
        SET ${updateFields.join(', ')} 
        WHERE tenant_id = ? AND insight_id = ?
      `;
      
      await this.client.execute(query, updateParams);
      
      // Get the updated insight
      return await this.getInsight(insightId);
    } catch (error) {
      console.error(`Error updating insight ${insightId}:`, error);
      throw error;
    }
  }

  /**
   * Delete an insight
   * @param {string} insightId - Insight ID
   * @returns {Promise<boolean>} - Success status
   */
  async deleteInsight(insightId) {
    try {
      const query = `
        DELETE FROM ${this.client.keyspace}.insights 
        WHERE tenant_id = ? AND insight_id = ?
      `;
      
      await this.client.execute(query, [this.tenantId, insightId]);
      
      return true;
    } catch (error) {
      console.error(`Error deleting insight ${insightId}:`, error);
      throw error;
    }
  }

  /**
   * Get insights related to a document
   * @param {string} docId - Document ID
   * @param {number} limit - Maximum number of results
   * @returns {Promise<Array>} - Related insights
   */
  async getRelatedInsights(docId, limit = 10) {
    try {
      const query = `
        SELECT * FROM ${this.client.keyspace}.insights 
        WHERE tenant_id = ? 
        AND source_ids CONTAINS ? 
        LIMIT ?
      `;
      
      const result = await this.client.execute(query, [
        this.tenantId,
        docId,
        limit
      ]);
      
      return result.rows.map(row => this._formatInsight(row));
    } catch (error) {
      console.error(`Error getting insights related to document ${docId}:`, error);
      throw error;
    }
  }

  /**
   * Format an insight from the database
   * @private
   * @param {Object} row - Database row
   * @returns {Object} - Formatted insight
   */
  _formatInsight(row) {
    return {
      id: row.insight_id.toString(),
      tenantId: row.tenant_id,
      title: row.title,
      description: row.description,
      sourceIds: row.source_ids ? row.source_ids.map(id => id.toString()) : [],
      createdAt: row.created_at,
      artifactUrls: row.artifact_urls || [],
      metadata: row.metadata || {}
    };
  }
}

module.exports = { InsightsService };
