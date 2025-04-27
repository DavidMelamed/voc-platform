/**
 * Real implementation of OpenAI API for embeddings and completions
 */
const { OpenAI } = require('openai');

class OpenAIClient {
  /**
   * Create a new OpenAI client
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    const apiKey = options.apiKey || process.env.OPENAI_API_KEY;
    
    if (!apiKey) {
      throw new Error('OpenAI API key is required');
    }
    
    this.client = new OpenAI({
      apiKey: apiKey,
      timeout: options.timeout || 60000, // 60 second timeout by default
      maxRetries: options.maxRetries || 3
    });
    
    this.embeddingModel = options.embeddingModel || 'text-embedding-ada-002';
    this.completionModel = options.completionModel || 'gpt-4';
    this.dimensions = options.dimensions || 1536; // Default for text-embedding-ada-002
    
    console.log(`OpenAI client initialized with embedding model: ${this.embeddingModel}`);
  }
  
  /**
   * Generate embeddings for a single text query
   * @param {string} text - Text to embed
   * @returns {Promise<Array<number>>} - Embedding vector
   */
  async embedQuery(text) {
    try {
      const response = await this.client.embeddings.create({
        model: this.embeddingModel,
        input: text
      });
      
      return response.data[0].embedding;
    } catch (error) {
      console.error('Error generating embedding:', error);
      throw error;
    }
  }
  
  /**
   * Generate embeddings for multiple documents
   * @param {Array<string>} documents - Documents to embed
   * @returns {Promise<Array<Array<number>>>} - Array of embedding vectors
   */
  async embedDocuments(documents) {
    try {
      // OpenAI allows multiple inputs in a single request
      const response = await this.client.embeddings.create({
        model: this.embeddingModel,
        input: documents
      });
      
      // Sort the results by index to ensure they match the input order
      const sortedEmbeddings = response.data
        .sort((a, b) => a.index - b.index)
        .map(item => item.embedding);
      
      return sortedEmbeddings;
    } catch (error) {
      console.error('Error generating document embeddings:', error);
      throw error;
    }
  }
  
  /**
   * Generate a text completion using the OpenAI API
   * @param {Object} params - Completion parameters
   * @returns {Promise<string>} - Generated text
   */
  async createCompletion(params) {
    try {
      const response = await this.client.chat.completions.create({
        model: params.model || this.completionModel,
        messages: params.messages || [{ role: 'user', content: params.prompt }],
        temperature: params.temperature || 0.7,
        max_tokens: params.max_tokens || 1000,
        top_p: params.top_p || 1,
        frequency_penalty: params.frequency_penalty || 0,
        presence_penalty: params.presence_penalty || 0
      });
      
      return response.choices[0].message.content;
    } catch (error) {
      console.error('Error generating completion:', error);
      throw error;
    }
  }
}

// For backward compatibility with the stub implementation
class OpenAIEmbeddings {
  constructor(params = {}) {
    this.client = new OpenAIClient(params);
    this.dimensions = params.dimensions || 1536;
  }
  
  async embedQuery(text) {
    return this.client.embedQuery(text);
  }
  
  async embedDocuments(documents) {
    return this.client.embedDocuments(documents);
  }
}

module.exports = {
  OpenAIClient,
  OpenAIEmbeddings
};
