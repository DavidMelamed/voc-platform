/**
 * Service for interacting with DataForSEO APIs through the MCP server
 */
class DataForSEOService {
  /**
   * Create a new DataForSEOService
   * @param {string} apiKey - DataForSEO API key
   * @param {string} login - DataForSEO login
   */
  constructor(apiKey, login) {
    this.apiKey = apiKey;
    this.login = login;
    this.baseUrl = 'https://api.dataforseo.com/v3';
    this.auth = Buffer.from(`${login}:${apiKey}`).toString('base64');
  }

  /**
   * Perform SERP Google Organic Live Advanced search
   * @param {string} keyword - Search query
   * @param {string} locationName - Location for search
   * @param {string} languageCode - Language code
   * @param {number} depth - Number of results
   * @returns {Promise<Object>} - Search results
   */
  async serpGoogleOrganicLiveAdvanced(keyword, locationName, languageCode, depth = 100) {
    console.log(`Performing DataForSEO SERP search for keyword: ${keyword}`);
    
    try {
      const url = `${this.baseUrl}/serp/google/organic/live/advanced`;
      const postData = [{
        keyword: keyword,
        location_name: locationName,
        language_code: languageCode,
        depth: depth
      }];
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.auth}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        throw new Error(`DataForSEO API error: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log(`DataForSEO request completed for keyword '${keyword}'`);
      return data;
    } catch (error) {
      console.error(`DataForSEO SERP search error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get search volume data for keywords
   * @param {Array<string>} keywords - Keywords to check
   * @param {string} locationName - Location for search
   * @param {string} languageCode - Language code
   * @returns {Promise<Object>} - Search volume data
   */
  async keywordsGoogleAdsSearchVolume(keywords, locationName, languageCode) {
    console.log(`Getting search volume for keywords: ${keywords.join(", ")}`);
    
    try {
      const url = `${this.baseUrl}/keywords_data/google_ads/search_volume/live`;
      const postData = [{
        keywords: keywords,
        location_name: locationName,
        language_code: languageCode
      }];
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.auth}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        throw new Error(`DataForSEO API error: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log(`Search volume data retrieved for ${keywords.length} keywords`);
      return data;
    } catch (error) {
      console.error(`DataForSEO search volume error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get domain ranked keywords
   * @param {string} target - Target domain
   * @param {string} locationName - Location name
   * @param {string} languageCode - Language code
   * @param {number} limit - Maximum results
   * @returns {Promise<Object>} - Domain ranked keywords
   */
  async dataLabsGoogleRankedKeywords(target, locationName, languageCode, limit = 10) {
    console.log(`Getting ranked keywords for domain: ${target}`);
    
    try {
      const url = `${this.baseUrl}/dataforseo_labs/google/ranked_keywords/live`;
      const postData = [{
        target: target,
        location_name: locationName,
        language_code: languageCode,
        limit: limit
      }];
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.auth}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        throw new Error(`DataForSEO API error: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log(`Ranked keywords retrieved for domain ${target}`);
      return data;
    } catch (error) {
      console.error(`DataForSEO ranked keywords error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get domain rank overview
   * @param {string} target - Target domain
   * @param {string} locationName - Location for search
   * @param {string} languageCode - Language code
   * @returns {Promise<Object>} - Domain rank overview
   */
  async dataLabsGoogleDomainRankOverview(target, locationName, languageCode) {
    console.log(`Getting domain rank overview for: ${target}`);
    
    try {
      const url = `${this.baseUrl}/dataforseo_labs/google/domain_rank_overview/live`;
      const postData = [{
        target: target,
        location_name: locationName,
        language_code: languageCode
      }];
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.auth}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        throw new Error(`DataForSEO API error: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log(`Domain rank overview retrieved for ${target}`);
      return data;
    } catch (error) {
      console.error(`DataForSEO domain rank overview error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get SERP competitors
   * @param {Array<string>} keywords - Keywords to analyze
   * @param {string} locationName - Location name
   * @param {string} languageCode - Language code
   * @param {number} limit - Number of results
   * @returns {Promise<Object>} - SERP competitors data
   */
  async dataLabsGoogleSerpCompetitors(keywords, locationName, languageCode, limit = 10) {
    console.log(`Getting SERP competitors for keywords: ${keywords.join(", ")}`);
    
    try {
      const url = `${this.baseUrl}/dataforseo_labs/google/serp_competitors/live`;
      const postData = [{
        keywords: keywords,
        location_name: locationName,
        language_code: languageCode,
        limit: limit
      }];
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.auth}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
      });
      
      if (!response.ok) {
        throw new Error(`DataForSEO API error: ${response.status} - ${await response.text()}`);
      }
      
      const data = await response.json();
      console.log(`SERP competitors data retrieved for ${keywords.length} keywords`);
      return data;
    } catch (error) {
      console.error(`DataForSEO SERP competitors error: ${error.message}`);
      throw error;
    }
  }
}

module.exports = { DataForSEOService };
