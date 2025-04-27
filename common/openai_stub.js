/**
 * Stub implementation of OpenAI embeddings to avoid API key requirements
 * during local development and testing without actual API calls.
 */
class OpenAIEmbeddings {
  constructor(params = {}) {
    this.dimensions = params.dimensions || 1536;
    console.log('Using stubbed OpenAIEmbeddings - no actual API calls will be made');
  }

  /**
   * Generate a mock embedding vector of the specified dimensions
   * Always returns a consistent vector based on the input text's hash
   * @param {string} text - Text to embed
   * @returns {Promise<Array<number>>} - Mock embedding vector
   */
  async embedQuery(text) {
    return this._generateStubVector(text);
  }

  /**
   * Generate a mock embedding vector for a document
   * @param {string} document - Document to embed
   * @returns {Promise<Array<number>>} - Mock embedding vector
   */
  async embedDocuments(documents) {
    return documents.map(doc => this._generateStubVector(doc));
  }

  /**
   * Generate a deterministic mock vector based on text content
   * @private
   * @param {string} text - Input text
   * @returns {Array<number>} - Mock embedding vector
   */
  _generateStubVector(text) {
    // Simple hash function to get a deterministic seed from text
    const seed = text.split('').reduce((acc, char) => {
      return (acc * 31 + char.charCodeAt(0)) % 1000000;
    }, 0);
    
    // Generate vector values based on seed
    const vector = new Array(this.dimensions).fill(0).map((_, i) => {
      const value = Math.sin(seed * (i + 1) * 0.01);
      return parseFloat(value.toFixed(6));
    });
    
    return vector;
  }
}

module.exports = { OpenAIEmbeddings };
