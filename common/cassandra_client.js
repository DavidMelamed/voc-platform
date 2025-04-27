/**
 * Real implementation of the Cassandra driver for Astra DB
 */
const cassandra = require('cassandra-driver');
const { mapping } = require('cassandra-driver');

/**
 * Create a Cassandra client configured for Astra DB
 * @param {Object} options - Configuration options
 * @returns {cassandra.Client} - Configured Cassandra client
 */
function createClient(options = {}) {
  // Ensure required environment variables are present
  const astraDbId = process.env.ASTRA_DB_ID;
  const astraRegion = process.env.ASTRA_DB_REGION;
  const astraToken = process.env.ASTRA_TOKEN;
  const keyspace = process.env.ASTRA_KEYSPACE || options.keyspace || 'voc_platform';
  
  if (!astraDbId || !astraRegion || !astraToken) {
    throw new Error('Missing required Astra DB environment variables');
  }
  
  // Create secure bundle
  const authProvider = new cassandra.auth.PlainTextAuthProvider(
    'token',
    astraToken
  );
  
  // Create the client with the secure connect bundle
  const client = new cassandra.Client({
    cloud: {
      secureConnectBundle: `https://${astraDbId}-${astraRegion}.apps.astra.datastax.com/api/rest/v1/auth/secure-connect-bundle`,
    },
    authProvider,
    keyspace,
    protocolOptions: {
      maxVersion: 4
    },
    socketOptions: {
      readTimeout: 30000
    },
    queryOptions: {
      consistency: cassandra.types.consistencies.localQuorum,
      isIdempotent: true
    },
    pooling: {
      coreConnectionsPerHost: {
        [cassandra.types.distance.local]: 2,
        [cassandra.types.distance.remote]: 1
      }
    }
  });
  
  console.log(`Created Cassandra client for Astra DB (ID: ${astraDbId}, Region: ${astraRegion})`);
  return client;
}

/**
 * Create a mapper for Cassandra ORM operations
 * @param {cassandra.Client} client - Cassandra client
 * @param {Object} models - Models definition
 * @returns {mapping.Mapper} - Configured mapper
 */
function createMapper(client, models) {
  return new mapping.Mapper(client, {
    models
  });
}

module.exports = {
  createClient,
  createMapper,
  // Re-export the original driver for use in other modules
  cassandra
};
