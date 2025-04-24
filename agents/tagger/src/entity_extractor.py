"""
Entity extraction utilities for the Tagger Agent.

This module provides functionality for extracting entities from text
using LLMs and categorizing them into predefined types.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from models import Entity, Topic, Brand, Person, Organization, Location, Product, Feature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Utility for extracting entities from text using LLMs.
    
    This class uses LLMs to identify and categorize entities in text
    according to predefined types (Topic, Brand, etc.).
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the entity extractor.
        
        Args:
            llm: Language model to use for extraction (optional)
        """
        self.llm = llm or ChatOpenAI(model="gpt-4o")
        self.entity_types = {
            "Topic": Topic,
            "Brand": Brand,
            "Person": Person,
            "Organization": Organization,
            "Location": Location,
            "Product": Product,
            "Feature": Feature
        }
        
        logger.info(f"Initialized EntityExtractor with model: {self.llm.model_name}")
        
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        try:
            # For large texts, we'll just use a portion to avoid token limits
            # In a real implementation, we might process the text in chunks
            # or use a different approach for long texts
            text_sample = text[:4000] if len(text) > 4000 else text
            
            # Create the prompt for entity extraction
            prompt = self._create_extraction_prompt(text_sample)
            
            # Call the LLM
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response
            return await self._parse_extraction_response(response.content)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
            
    def _create_extraction_prompt(self, text: str) -> str:
        """
        Create a prompt for entity extraction.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Prompt for the LLM
        """
        return f"""
        Please analyze the following text and extract all relevant entities into the following categories:
        - Topic: Main subjects or themes discussed in the text
        - Brand: Company or product brand names mentioned
        - Person: Names of individuals mentioned
        - Organization: Names of companies, institutions, or other organizations
        - Location: Places, cities, countries, or geographical locations
        - Product: Specific products mentioned
        - Feature: Features, characteristics, or attributes of products/services
        
        TEXT:
        {text}
        
        Return the results in a JSON format like this:
        {{
            "entities": [
                {{"name": "entity name", "entity_type": "Topic", "confidence": 0.9}},
                {{"name": "entity name", "entity_type": "Brand", "confidence": 0.8}},
                ...
            ]
        }}
        
        Include only entities that are clearly present in the text. Assign a confidence score between 0 and 1.
        Please respond with ONLY the JSON object and nothing else.
        """
        
    async def _parse_extraction_response(self, response_text: str) -> List[Entity]:
        """
        Parse the LLM response into Entity objects.
        
        Args:
            response_text: LLM response text
            
        Returns:
            List of extracted entities
        """
        try:
            # Extract JSON from response text
            json_text = self._extract_json_from_text(response_text)
            
            if not json_text:
                logger.warning("Failed to extract JSON from LLM response")
                return []
                
            # Parse JSON
            data = json.loads(json_text)
            
            if not isinstance(data, dict) or "entities" not in data:
                logger.warning("Invalid JSON structure in LLM response")
                return []
                
            # Convert to Entity objects
            entities = []
            
            for entity_data in data["entities"]:
                try:
                    name = entity_data.get("name", "").strip()
                    entity_type = entity_data.get("entity_type", "Topic")
                    confidence = float(entity_data.get("confidence", 1.0))
                    
                    # Skip empty entities
                    if not name:
                        continue
                        
                    # Ensure entity type is valid
                    if entity_type not in self.entity_types:
                        logger.warning(f"Invalid entity type: {entity_type}, defaulting to Topic")
                        entity_type = "Topic"
                        
                    # Create entity object
                    entity_class = self.entity_types[entity_type]
                    entity = entity_class(name=name, confidence=confidence)
                    entities.append(entity)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing entity: {str(e)}")
                    continue
                    
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing extraction response: {str(e)}")
            return []
            
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract JSON from text.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON text
        """
        # First, check if the text is already valid JSON
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
            
        # Try to extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, text)
        
        if matches:
            # Try each match until we find valid JSON
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
                    
        # Try to find anything that looks like JSON with curly braces
        json_pattern = r'({[\s\S]*?})'
        matches = re.findall(json_pattern, text)
        
        if matches:
            # Try each match until we find valid JSON
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
                    
        # No valid JSON found
        return ""
