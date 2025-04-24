const { v4: uuidv4 } = require('uuid');

/**
 * Service for managing raw documents
 */
class RawDocService {
  /**
   * Create a new RawDocService
   * @param {CassandraClient} client - Astra DB client
   * @param {string} tenantId - Tenant ID for data partitioning
   */
  constructor(client, tenantId) {
    this.client = client;
    this.tenantId = tenantId;
  }

  /**
   * Get a document by ID
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} - Document data
   */
  async getDocument(docId) {
    try {
      const result = await this.client.executePrepared('getRawDoc', [
        this.tenantId,
        docId
      ]);
      
      if (result.rowLength === 0) {
        throw new Error(`Document not found: ${docId}`);
      }
      
      return this._formatDocument(result.first());
    } catch (error) {
      console.error(`Error getting document ${docId}:`, error);
      throw error;
    }
  }

  /**
   * List documents with optional filtering
   * @param {string} sourceType - Optional source type filter
   * @param {number} limit - Maximum number of results
   * @param {string} lastKey - Pagination token
   * @returns {Promise<Object>} - List of documents with pagination info
   */
  async listDocuments(sourceType, limit = 10, lastKey = null) {
    try {
      let query;
      let params;
      
      if (sourceType) {
        // Filter by source type
        query = `
          SELECT * FROM ${this.client.keyspace}.raw_docs 
          WHERE tenant_id = ? AND source_type = ?
        `;
        params = [this.tenantId, sourceType];
      } else {
        // List all documents
        query = `
          SELECT * FROM ${this.client.keyspace}.raw_docs 
          WHERE tenant_id = ?
        `;
        params = [this.tenantId];
      }
      
      // Add pagination if last key provided
      if (lastKey) {
        query += ` AND token(doc_id) > token(?)`;
        params.push(lastKey);
      }
      
      // Add limit
      query += ` LIMIT ?`;
      params.push(limit);
      
      const result = await this.client.execute(query, params);
      
      // Get the last document ID for pagination
      let nextPageToken = null;
      if (result.rows.length === limit) {
        nextPageToken = result.rows[result.rows.length - 1].doc_id.toString();
      }
      
      return {
        documents: result.rows.map(row => this._formatDocument(row)),
        pagination: {
          nextPageToken,
          count: result.rows.length
        }
      };
    } catch (error) {
      console.error('Error listing documents:', error);
      throw error;
    }
  }

  /**
   * Create a new document
   * @param {string} sourceType - Source type
   * @param {string} content - Document content
   * @param {Object} metadata - Additional metadata
   * @returns {Promise<Object>} - Created document
   */
  async createDocument(sourceType, content, metadata = {}) {
    try {
      const docId = uuidv4();
      const now = new Date();
      
      const query = `
        INSERT INTO ${this.client.keyspace}.raw_docs (
          tenant_id, doc_id, source_type, content, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `;
      
      await this.client.execute(query, [
        this.tenantId,
        docId,
        sourceType,
        content,
        metadata,
        now,
        now
      ]);
      
      return {
        id: docId,
        tenantId: this.tenantId,
        sourceType,
        content,
        metadata,
        createdAt: now,
        updatedAt: now
      };
    } catch (error) {
      console.error('Error creating document:', error);
      throw error;
    }
  }

  /**
   * Update an existing document
   * @param {string} docId - Document ID
   * @param {Object} updates - Fields to update
   * @returns {Promise<Object>} - Updated document
   */
  async updateDocument(docId, updates) {
    try {
      // Get the current document
      const current = await this.getDocument(docId);
      
      // Prepare update fields
      const now = new Date();
      const updateFields = [];
      const updateParams = [this.tenantId, docId];
      
      if (updates.content !== undefined) {
        updateFields.push('content = ?');
        updateParams.push(updates.content);
      }
      
      if (updates.sourceType !== undefined) {
        updateFields.push('source_type = ?');
        updateParams.push(updates.sourceType);
      }
      
      if (updates.metadata !== undefined) {
        updateFields.push('metadata = ?');
        updateParams.push({
          ...current.metadata,
          ...updates.metadata
        });
      }
      
      // Always update the updated_at timestamp
      updateFields.push('updated_at = ?');
      updateParams.push(now);
      
      // Build and execute query
      const query = `
        UPDATE ${this.client.keyspace}.raw_docs 
        SET ${updateFields.join(', ')} 
        WHERE tenant_id = ? AND doc_id = ?
      `;
      
      await this.client.execute(query, updateParams);
      
      // Get the updated document
      return await this.getDocument(docId);
    } catch (error) {
      console.error(`Error updating document ${docId}:`, error);
      throw error;
    }
  }

  /**
   * Delete a document
   * @param {string} docId - Document ID
   * @returns {Promise<boolean>} - Success status
   */
  async deleteDocument(docId) {
    try {
      const query = `
        DELETE FROM ${this.client.keyspace}.raw_docs 
        WHERE tenant_id = ? AND doc_id = ?
      `;
      
      await this.client.execute(query, [this.tenantId, docId]);
      
      return true;
    } catch (error) {
      console.error(`Error deleting document ${docId}:`, error);
      throw error;
    }
  }

  /**
   * Search documents by content
   * @param {string} searchText - Text to search for
   * @param {number} limit - Maximum number of results
   * @returns {Promise<Array>} - Matching documents
   */
  async searchDocuments(searchText, limit = 10) {
    try {
      // This is a basic implementation using LIKE
      // A production version would use a proper search index
      const query = `
        SELECT * FROM ${this.client.keyspace}.raw_docs 
        WHERE tenant_id = ? 
        AND content LIKE ? 
        LIMIT ?
      `;
      
      const result = await this.client.execute(query, [
        this.tenantId,
        `%${searchText}%`,
        limit
      ]);
      
      return result.rows.map(row => this._formatDocument(row));
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  /**
   * Format a document from the database
   * @private
   * @param {Object} row - Database row
   * @returns {Object} - Formatted document
   */
  _formatDocument(row) {
    return {
      id: row.doc_id.toString(),
      tenantId: row.tenant_id,
      sourceType: row.source_type,
      content: row.content,
      metadata: row.metadata || {},
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }
}

module.exports = { RawDocService };
