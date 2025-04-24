"""
Tagger Agent for Voice-of-Customer & Brand-Intel Platform.

This agent is responsible for:
1. Validating output with Pydantic models
2. Generating OpenAI or Instructor-XL embeddings
3. Upserting data (doc_id, tenant_id, embedding, meta) into Astra vector table
4. Creating graph edges:
   - (FeedbackItem)-[:MENTIONS]->(Topic)
   - (FeedbackItem)-[:ABOUT]->(Brand)
"""

import os
import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field, validator

from pulsar_client import PulsarClient
from astra_client import AstraClient
from text_chunker import TextChunker
from entity_extractor import EntityExtractor
from models import FeedbackItem, Topic, Brand, EmbeddedChunk

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize clients
pulsar_client = PulsarClient()
astra_client = AstraClient()

# Initialize components
llm = ChatOpenAI(model="gpt-4o")
embeddings = OpenAIEmbeddings()
text_chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
entity_extractor = EntityExtractor(llm=llm)

class TaggerAgent:
    """
    Agent for processing and tagging content from scraped documents.
    
    This agent processes scraped content, extracts entities, creates embeddings,
    and stores the results in Astra DB.
    """
    
    def __init__(self):
        """Initialize the tagger agent."""
        self.tenant_id = os.getenv("TENANT_ID", "default")
        self.embedding_dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        self.sentiment_threshold = float(os.getenv("SENTIMENT_THRESHOLD", "0.5"))
        self.urgency_threshold = float(os.getenv("URGENCY_THRESHOLD", "0.7"))
        
        logger.info(f"Initialized TaggerAgent for tenant {self.tenant_id}")
        
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a scraped document.
        
        Args:
            document: Scraped document data
            
        Returns:
            Processing results
        """
        logger.info(f"Processing document: {document.get('job_id', 'unknown')}")
        
        try:
            # Extract fields from the document
            job_id = document.get("job_id", str(uuid.uuid4()))
            source_type = document.get("source_type", "unknown")
            content = document.get("content", document.get("result", {}).get("content", ""))
            metadata = document.get("metadata", {})
            
            # Validate the content
            if not content or len(content) < 10:
                raise ValueError("Document content is too short or missing")
                
            # Chunk the text
            chunks = await text_chunker.chunk_text(content)
            logger.info(f"Created {len(chunks)} chunks from document")
            
            # Process each chunk
            results = []
            for i, chunk in enumerate(chunks):
                chunk_result = await self._process_chunk(
                    job_id=job_id,
                    chunk_id=f"{job_id}-chunk-{i}",
                    text=chunk,
                    source_type=source_type,
                    metadata=metadata
                )
                results.append(chunk_result)
                
            # Create the feedback item for the full document
            feedback_item = await self._create_feedback_item(
                job_id=job_id,
                text=content,
                source_type=source_type,
                metadata=metadata,
                chunk_results=results
            )
            
            # Create graph edges
            edges = await self._create_graph_edges(feedback_item)
            
            # Return the results
            return {
                "job_id": job_id,
                "tenant_id": self.tenant_id,
                "doc_id": feedback_item.doc_id,
                "sentiment": feedback_item.sentiment,
                "topics": [topic.name for topic in feedback_item.topics],
                "urgency": feedback_item.urgency,
                "source_type": source_type,
                "chunks": len(chunks),
                "embeddings": len(results),
                "edges": len(edges),
                "metadata": metadata,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "job_id": document.get("job_id", "unknown"),
                "tenant_id": self.tenant_id,
                "error": str(e),
                "status": "error"
            }
            
    async def _process_chunk(self, job_id: str, chunk_id: str, text: str, source_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single text chunk.
        
        Args:
            job_id: Job ID
            chunk_id: Chunk ID
            text: Chunk text
            source_type: Source type
            metadata: Document metadata
            
        Returns:
            Chunk processing results
        """
        # Generate embedding
        embedding_vector = await self._generate_embedding(text)
        
        # Extract entities
        entities = await entity_extractor.extract_entities(text)
        
        # Create the embedded chunk object
        chunk = EmbeddedChunk(
            tenant_id=self.tenant_id,
            doc_id=job_id,
            chunk_id=chunk_id,
            text=text,
            embedding=embedding_vector,
            source_type=source_type,
            entities=entities,
            metadata=metadata
        )
        
        # Store in Astra DB
        await astra_client.store_vector(
            tenant_id=self.tenant_id,
            doc_id=job_id,
            chunk_id=chunk_id,
            text=text,
            embedding=embedding_vector,
            metadata={
                "source_type": source_type,
                "entities": json.dumps([e.dict() for e in entities]),
                **metadata
            }
        )
        
        return {
            "chunk_id": chunk_id,
            "entities": entities,
            "embedding_size": len(embedding_vector)
        }
        
    async def _create_feedback_item(
        self, 
        job_id: str, 
        text: str, 
        source_type: str, 
        metadata: Dict[str, Any],
        chunk_results: List[Dict[str, Any]]
    ) -> FeedbackItem:
        """
        Create a feedback item for the full document.
        
        Args:
            job_id: Job ID
            text: Full document text
            source_type: Source type
            metadata: Document metadata
            chunk_results: Results from processing each chunk
            
        Returns:
            FeedbackItem object
        """
        # Analyze sentiment and urgency
        sentiment_analysis = await self._analyze_sentiment(text)
        
        # Extract all entities from chunks
        all_topics = set()
        all_brands = set()
        
        for chunk in chunk_results:
            for entity in chunk["entities"]:
                if entity.entity_type == "Topic":
                    all_topics.add(entity.name)
                elif entity.entity_type == "Brand":
                    all_brands.add(entity.name)
        
        # Create topic and brand objects
        topics = [Topic(name=topic_name) for topic_name in all_topics]
        brands = [Brand(name=brand_name) for brand_name in all_brands]
        
        # Create feedback item
        feedback_item = FeedbackItem(
            tenant_id=self.tenant_id,
            doc_id=job_id,
            text=text,
            sentiment=sentiment_analysis["sentiment"],
            urgency=sentiment_analysis["urgency"],
            source_type=source_type,
            topics=topics,
            brands=brands,
            created_at=datetime.now().isoformat(),
            metadata=metadata
        )
        
        # Store feedback item in Astra DB
        await astra_client.store_raw_doc(
            tenant_id=self.tenant_id,
            doc_id=job_id,
            source_type=source_type,
            content=text,
            metadata={
                "sentiment": sentiment_analysis["sentiment"],
                "urgency": sentiment_analysis["urgency"],
                "topics": [topic.name for topic in topics],
                "brands": [brand.name for brand in brands],
                **metadata
            }
        )
        
        return feedback_item
        
    async def _create_graph_edges(self, feedback_item: FeedbackItem) -> List[Dict[str, Any]]:
        """
        Create graph edges for the feedback item.
        
        Args:
            feedback_item: FeedbackItem object
            
        Returns:
            List of created edges
        """
        edges = []
        
        # Create edges for topics
        for topic in feedback_item.topics:
            edge = await astra_client.create_edge(
                tenant_id=self.tenant_id,
                from_id=feedback_item.doc_id,
                to_id=str(uuid.uuid4()),  # In a real implementation, we would use a consistent ID for topics
                relation_type="MENTIONS",
                properties={
                    "entity_type": "Topic",
                    "entity_name": topic.name,
                    "created_at": datetime.now().isoformat()
                }
            )
            edges.append(edge)
            
        # Create edges for brands
        for brand in feedback_item.brands:
            edge = await astra_client.create_edge(
                tenant_id=self.tenant_id,
                from_id=feedback_item.doc_id,
                to_id=str(uuid.uuid4()),  # In a real implementation, we would use a consistent ID for brands
                relation_type="ABOUT",
                properties={
                    "entity_type": "Brand",
                    "entity_name": brand.name,
                    "created_at": datetime.now().isoformat()
                }
            )
            edges.append(edge)
            
        return edges
        
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # In a real implementation, this would support different embedding models
            embedding = await embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * self.embedding_dimensions
            
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment and urgency of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        try:
            # This is a simplified implementation
            # In a real system, this would use a proper sentiment analysis model
            
            # Use the LLM to determine sentiment and urgency
            prompt = f"""
            Please analyze the following text for sentiment and urgency:
            
            Text: {text[:1000]}... [truncated]
            
            Return only a JSON object with:
            - sentiment: "positive", "neutral", or "negative"
            - urgency: true or false (whether this requires urgent attention)
            """
            
            response = await llm.ainvoke(prompt)
            
            # Parse the response
            try:
                # Extract JSON from the response
                json_text = response.content.strip()
                if json_text.startswith("```json"):
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                elif json_text.startswith("```"):
                    json_text = json_text.split("```")[1].split("```")[0].strip()
                    
                result = json.loads(json_text)
                return {
                    "sentiment": result.get("sentiment", "neutral"),
                    "urgency": result.get("urgency", False)
                }
            except (json.JSONDecodeError, IndexError):
                # Fallback to default values
                return {
                    "sentiment": "neutral",
                    "urgency": False
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "sentiment": "neutral",
                "urgency": False
            }
            
    async def start(self):
        """Start the tagger agent service."""
        logger.info("Starting Tagger Agent service")
        
        # Connect to Pulsar
        await pulsar_client.connect()
        
        # Create consumer
        await pulsar_client.create_consumer("scrape.results", "tagger-consumer")
        
        # Main processing loop
        try:
            while True:
                # Get next document
                message = await pulsar_client.receive_message("scrape.results")
                
                if message:
                    # Parse document data
                    try:
                        document = json.loads(message.data().decode("utf-8"))
                        
                        # Process the document
                        result = await self.process_document(document)
                        
                        # Send result to tag.complete topic
                        await pulsar_client.send_message(
                            "tag.complete", 
                            json.dumps(result).encode("utf-8")
                        )
                        
                        # Acknowledge the message
                        await pulsar_client.acknowledge(message)
                        
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in message")
                        # Acknowledge the message to avoid infinite retry
                        await pulsar_client.acknowledge(message)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        # Acknowledge the message to avoid infinite retry
                        await pulsar_client.acknowledge(message)
                else:
                    # No documents available, sleep before checking again
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Stopping Tagger Agent service")
        finally:
            # Close Pulsar connection
            await pulsar_client.close()
            
if __name__ == "__main__":
    # Create and start the tagger agent
    tagger = TaggerAgent()
    asyncio.run(tagger.start())
