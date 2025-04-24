/**
 * Service for performing graph operations and queries
 */
class GraphService {
  /**
   * Create a new GraphService
   * @param {CassandraClient} client - Astra DB client
   * @param {string} tenantId - Tenant ID for data partitioning
   */
  constructor(client, tenantId) {
    this.client = client;
    this.tenantId = tenantId;
  }

  /**
   * Query the graph for relationships
   * @param {string} fromType - Entity type for the starting node
   * @param {string} relation - Relationship type to traverse
   * @param {string} toType - Entity type for the ending node
   * @param {string} fromId - Optional ID of the starting node
   * @param {string} toId - Optional ID of the ending node
   * @param {number} limit - Maximum number of results
   * @returns {Promise<Array>} - Query results
   */
  async query(fromType, relation, toType, fromId, toId, limit = 10) {
    try {
      let queryParams = [this.tenantId];
      let queryString = '';
      
      // Build query based on provided parameters
      if (fromId && toId) {
        // Direct relationship query
        queryString = `
          SELECT * FROM ${this.client.keyspace}.graph_edges 
          WHERE tenant_id = ? 
          AND from_id = ? 
          AND relation_type = ? 
          AND to_id = ?
        `;
        queryParams.push(fromId, relation, toId);
      } else if (fromId) {
        // Outgoing relationships from a specific node
        queryString = `
          SELECT * FROM ${this.client.keyspace}.graph_edges 
          WHERE tenant_id = ? 
          AND from_id = ? 
          AND relation_type = ?
          LIMIT ?
        `;
        queryParams.push(fromId, relation, limit);
      } else if (toId) {
        // Incoming relationships to a specific node
        // Note: This requires a secondary index on to_id
        queryString = `
          SELECT * FROM ${this.client.keyspace}.graph_edges 
          WHERE tenant_id = ? 
          AND to_id = ? 
          AND relation_type = ?
          LIMIT ?
        `;
        queryParams.push(toId, relation, limit);
      } else {
        // General relationship query
        queryString = `
          SELECT * FROM ${this.client.keyspace}.graph_edges 
          WHERE tenant_id = ? 
          AND relation_type = ?
          LIMIT ?
        `;
        queryParams.push(relation, limit);
      }
      
      const result = await this.client.execute(queryString, queryParams);
      
      return result.rows.map(row => this._formatEdgeResult(row));
    } catch (error) {
      console.error('Graph query error:', error);
      throw error;
    }
  }

  /**
   * Find paths between nodes
   * @param {string} startId - ID of the starting node
   * @param {string} endId - ID of the ending node
   * @param {number} maxDepth - Maximum path depth
   * @returns {Promise<Array>} - Paths found
   */
  async findPaths(startId, endId, maxDepth = 3) {
    try {
      // This is a simplified implementation
      // A real implementation would use a graph traversal algorithm
      // or leverage Astra's graph capabilities
      
      // For now, we'll just return a direct path if it exists
      const directPath = await this.query(null, null, null, startId, endId, 1);
      
      if (directPath.length > 0) {
        return [{
          path: [directPath[0]],
          length: 1
        }];
      }
      
      // If maxDepth > 1, we could implement a breadth-first search here
      // to find multi-hop paths
      
      return [];
    } catch (error) {
      console.error('Find paths error:', error);
      throw error;
    }
  }

  /**
   * Create a new edge in the graph
   * @param {string} fromId - ID of the source node
   * @param {string} toId - ID of the target node
   * @param {string} relationType - Type of relationship
   * @param {number} weight - Edge weight (0-1)
   * @param {Object} properties - Additional edge properties
   * @returns {Promise<Object>} - Created edge
   */
  async createEdge(fromId, toId, relationType, weight = 1.0, properties = {}) {
    try {
      const query = `
        INSERT INTO ${this.client.keyspace}.graph_edges (
          tenant_id, from_id, relation_type, to_id, weight, properties
        ) VALUES (?, ?, ?, ?, ?, ?)
      `;
      
      await this.client.execute(query, [
        this.tenantId,
        fromId,
        relationType,
        toId,
        weight,
        properties
      ]);
      
      return {
        from: fromId,
        to: toId,
        type: relationType,
        weight,
        properties
      };
    } catch (error) {
      console.error('Create edge error:', error);
      throw error;
    }
  }

  /**
   * Delete an edge from the graph
   * @param {string} fromId - ID of the source node
   * @param {string} toId - ID of the target node
   * @param {string} relationType - Type of relationship
   * @returns {Promise<boolean>} - Success status
   */
  async deleteEdge(fromId, toId, relationType) {
    try {
      const query = `
        DELETE FROM ${this.client.keyspace}.graph_edges 
        WHERE tenant_id = ? 
        AND from_id = ? 
        AND relation_type = ? 
        AND to_id = ?
      `;
      
      await this.client.execute(query, [
        this.tenantId,
        fromId,
        relationType,
        toId
      ]);
      
      return true;
    } catch (error) {
      console.error('Delete edge error:', error);
      throw error;
    }
  }

  /**
   * Get most connected entities
   * @param {string} entityType - Type of entity
   * @param {number} limit - Maximum number of results
   * @returns {Promise<Array>} - Most connected entities
   */
  async getMostConnected(entityType, limit = 10) {
    try {
      // This would typically use an analytics query
      // For now, we'll just return a placeholder implementation
      
      const query = `
        SELECT from_id, COUNT(*) as connection_count
        FROM ${this.client.keyspace}.graph_edges
        WHERE tenant_id = ?
        GROUP BY from_id
        LIMIT ?
      `;
      
      const result = await this.client.execute(query, [this.tenantId, limit]);
      
      return result.rows.map(row => ({
        id: row.from_id.toString(),
        connectionCount: row.connection_count
      }));
    } catch (error) {
      console.error('Get most connected error:', error);
      throw error;
    }
  }

  /**
   * Format an edge result
   * @private
   * @param {Object} row - Database row
   * @returns {Object} - Formatted edge
   */
  _formatEdgeResult(row) {
    return {
      from: row.from_id.toString(),
      to: row.to_id.toString(),
      type: row.relation_type,
      weight: row.weight,
      properties: row.properties || {}
    };
  }
}

module.exports = { GraphService };
