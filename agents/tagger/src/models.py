"""
Data models for the Tagger Agent.

This module defines the Pydantic models used for validating and 
structuring data in the Voice-of-Customer platform.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union
from pydantic import BaseModel, Field, validator
import uuid

class Entity(BaseModel):
    """Base class for entities extracted from text."""
    name: str = Field(..., description="Name of the entity")
    entity_type: str = Field(..., description="Type of entity (e.g., 'Topic', 'Brand')")
    confidence: float = Field(default=1.0, description="Confidence score for the entity extraction")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate that the name is not empty."""
        if not v or not v.strip():
            raise ValueError("Entity name cannot be empty")
        return v.strip()
        
    @validator('entity_type')
    def validate_entity_type(cls, v):
        """Validate that the entity type is valid."""
        valid_types = {"Topic", "Brand", "Person", "Organization", "Location", "Product", "Feature"}
        if v not in valid_types:
            raise ValueError(f"Entity type must be one of: {', '.join(valid_types)}")
        return v
        
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

class Topic(Entity):
    """Topic entity extracted from text."""
    entity_type: str = Field(default="Topic", const=True)
    
class Brand(Entity):
    """Brand entity extracted from text."""
    entity_type: str = Field(default="Brand", const=True)
    
class Person(Entity):
    """Person entity extracted from text."""
    entity_type: str = Field(default="Person", const=True)
    
class Organization(Entity):
    """Organization entity extracted from text."""
    entity_type: str = Field(default="Organization", const=True)
    
class Location(Entity):
    """Location entity extracted from text."""
    entity_type: str = Field(default="Location", const=True)
    
class Product(Entity):
    """Product entity extracted from text."""
    entity_type: str = Field(default="Product", const=True)
    
class Feature(Entity):
    """Feature entity extracted from text."""
    entity_type: str = Field(default="Feature", const=True)

class EmbeddedChunk(BaseModel):
    """Chunk of text with embedding and metadata."""
    tenant_id: str = Field(..., description="Tenant ID")
    doc_id: str = Field(..., description="Document ID")
    chunk_id: str = Field(..., description="Chunk ID")
    text: str = Field(..., description="Text content of the chunk")
    embedding: List[float] = Field(..., description="Vector embedding of the text")
    source_type: str = Field(..., description="Type of source (e.g., 'website', 'review', 'social')")
    entities: List[Entity] = Field(default_factory=list, description="Entities extracted from the text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate that the text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        return v
        
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate that the embedding is not empty."""
        if not v or len(v) == 0:
            raise ValueError("Embedding cannot be empty")
        return v
        
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

class FeedbackItem(BaseModel):
    """Feedback item representing a document with sentiment, topics, etc."""
    tenant_id: str = Field(..., description="Tenant ID")
    doc_id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Full text content")
    sentiment: str = Field(..., description="Sentiment of the feedback (positive, neutral, negative)")
    urgency: bool = Field(default=False, description="Whether the feedback requires urgent attention")
    source_type: str = Field(..., description="Type of source (e.g., 'website', 'review', 'social')")
    topics: List[Topic] = Field(default_factory=list, description="Topics mentioned in the feedback")
    brands: List[Brand] = Field(default_factory=list, description="Brands mentioned in the feedback")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp when the feedback was created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Validate that the sentiment is valid."""
        valid_sentiments = {"positive", "neutral", "negative"}
        if v not in valid_sentiments:
            raise ValueError(f"Sentiment must be one of: {', '.join(valid_sentiments)}")
        return v
        
    @validator('text')
    def validate_text(cls, v):
        """Validate that the text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        return v
        
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

class GraphEdge(BaseModel):
    """Edge in the knowledge graph."""
    tenant_id: str = Field(..., description="Tenant ID")
    from_id: str = Field(..., description="ID of the source node")
    to_id: str = Field(..., description="ID of the target node")
    relation_type: str = Field(..., description="Type of relationship")
    weight: float = Field(default=1.0, description="Weight/strength of the relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the edge")
    
    @validator('relation_type')
    def validate_relation_type(cls, v):
        """Validate that the relation type is valid."""
        valid_relations = {"MENTIONS", "ABOUT", "RELATED_TO", "SAME_AS", "PART_OF"}
        if v not in valid_relations:
            raise ValueError(f"Relation type must be one of: {', '.join(valid_relations)}")
        return v
        
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
