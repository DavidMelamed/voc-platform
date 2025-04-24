/**
 * Langfuse configuration for the Voice-of-Customer & Brand-Intel Platform.
 * 
 * This file contains the setup for Langfuse, an open-source LLM observability
 * and analytics platform that helps track, monitor, and improve LLM applications.
 */

const { Langfuse } = require('langfuse');

/**
 * Initialize Langfuse client.
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.tenantId - Current tenant ID
 * @returns {Langfuse} - Configured Langfuse client
 */
function initLangfuse(options = {}) {
  const langfuse = new Langfuse({
    publicKey: process.env.LANGFUSE_PUBLIC_KEY,
    secretKey: process.env.LANGFUSE_SECRET_KEY,
    baseUrl: process.env.LANGFUSE_HOST || 'https://cloud.langfuse.com',
    flushAt: parseInt(process.env.LANGFUSE_FLUSH_AT || '20'),
    flushInterval: parseInt(process.env.LANGFUSE_FLUSH_INTERVAL || '5000'),
    debug: process.env.NODE_ENV !== 'production',
  });

  // Add tenant information to all traces
  if (options.tenantId) {
    langfuse.setUserId(options.tenantId);
  }

  return langfuse;
}

/**
 * Create a new trace for an agent operation
 * 
 * @param {Langfuse} langfuse - Langfuse client
 * @param {string} name - Name of the trace
 * @param {Object} metadata - Additional metadata for the trace
 * @returns {Object} - Trace object
 */
function createAgentTrace(langfuse, name, metadata = {}) {
  return langfuse.trace({
    name,
    metadata: {
      environment: process.env.NODE_ENV || 'development',
      ...metadata,
    },
    tags: [metadata.agentType || 'unknown', metadata.taskType || 'unknown'],
  });
}

/**
 * Log an observation to Langfuse
 * 
 * @param {Object} trace - Langfuse trace object
 * @param {string} name - Name of the observation
 * @param {Object} observation - Observation data
 */
function logObservation(trace, name, observation) {
  trace.observation({
    name,
    ...observation
  });
}

/**
 * Create and log a span for measuring duration of operations
 * 
 * @param {Object} trace - Langfuse trace object
 * @param {string} name - Name of the span
 * @param {Object} metadata - Additional metadata for the span
 * @returns {Object} - Span object
 */
function startSpan(trace, name, metadata = {}) {
  return trace.span({
    name,
    metadata,
    start: Date.now(),
  });
}

/**
 * End a span with result information
 * 
 * @param {Object} span - Langfuse span object
 * @param {string} status - Status of the operation (success, error)
 * @param {Object} metadata - Additional metadata about the result
 */
function endSpan(span, status, metadata = {}) {
  span.end({
    status,
    metadata,
    end: Date.now(),
  });
}

/**
 * Log an LLM call to Langfuse
 * 
 * @param {Object} trace - Langfuse trace object
 * @param {string} name - Name of the generation
 * @param {Object} params - LLM parameters
 * @param {Object} result - LLM response
 * @param {number} startTime - Start timestamp
 * @param {number} endTime - End timestamp
 * @param {Object} metadata - Additional metadata
 */
function logLLMGeneration(trace, name, params, result, startTime, endTime, metadata = {}) {
  trace.generation({
    name,
    model: params.model || 'unknown',
    modelParameters: params,
    prompt: params.prompt || params.messages,
    completion: result.content || result.text,
    startTime,
    endTime,
    metadata,
    usage: result.usage || {
      promptTokens: 0,
      completionTokens: 0,
      totalTokens: 0,
    },
  });
}

/**
 * Score an LLM generation for quality metrics
 * 
 * @param {Object} trace - Langfuse trace object
 * @param {string} generationId - ID of the generation to score
 * @param {string} name - Name of the score
 * @param {number} value - Score value (0-1)
 * @param {Object} metadata - Additional context about the score
 */
function scoreGeneration(trace, generationId, name, value, metadata = {}) {
  trace.score({
    name,
    value,
    traceId: trace.id,
    generationId,
    metadata,
  });
}

module.exports = {
  initLangfuse,
  createAgentTrace,
  logObservation,
  startSpan,
  endSpan,
  logLLMGeneration,
  scoreGeneration,
};
