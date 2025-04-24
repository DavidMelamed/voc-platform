"""
Astra DB client for the Tagger Agent.

This module provides a client for interacting with DataStax Astra DB
for storing documents, embeddings, and graph relationships.
"""

import os
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AstraClient:
    """
    Client for interacting with Astra DB services.
    
    This client provides methods for storing and retrieving documents,
    vectors, and graph relationships in Astra DB.
    """
    
    def __init__(self):
        """Initialize the Astra DB client."""
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.api_endpoint = os.getenv("ASTRA_API_ENDPOINT", "")
        self.token = os.getenv("ASTRA_TOKEN", "")
        self.keyspace = os.getenv("ASTRA_KEYSPACE", "voc_platform")
        
        if not self.api_endpoint and not self.mcp_server_url:
            logger.warning("Neither ASTRA_API_ENDPOINT nor MCP_SERVER_URL set. Using MCP fallback.")
            
        logger.info("Initialized AstraClient")
        
    async def store_raw_doc(self, tenant_id: str, doc_id: str, source_type: str, 
                           content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a raw document in Astra DB.
        
        Args:
            tenant_id: Tenant ID
            doc_id: Document ID
            source_type: Source type
            content: Document content
            metadata: Additional metadata
            
        Returns:
            Result of the operation
        """
        logger.info(f"Storing raw document: {doc_id} for tenant: {tenant_id}")
        
        try:
            # Use MCP server if endpoint not provided directly
            if not self.api_endpoint:
                return await self._call_mcp_tool("create_raw_doc", {
                    "tenantId": tenant_id,
                    "docId": doc_id,
                    "sourceType": source_type,
                    "content": content,
                    "metadata": metadata or {}
                })
                
            # Direct API call to Astra
            headers = {
                "Content-Type": "application/json",
                "X-Cassandra-Token": self.token
            }
            
            url = f"{self.api_endpoint}/api/rest/v2/keyspaces/{self.keyspace}/raw_docs"
            
            data = {
                "tenant_id": tenant_id,
                "doc_id": doc_id,
                "source_type": source_type,
                "content": content,
                "metadata": metadata or {},
                "created_at": "2023-04-23T00:00:00Z",  # Actual timestamp would be current
                "updated_at": "2023-04-23T00:00:00Z"   # Actual timestamp would be current
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 201:
                        return {
                            "success": True,
                            "doc_id": doc_id
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error storing raw document: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Error storing raw document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def store_vector(self, tenant_id: str, doc_id: str, chunk_id: str, 
                          text: str, embedding: List[float],
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a vector embedding in Astra DB.
        
        Args:
            tenant_id: Tenant ID
            doc_id: Document ID
            chunk_id: Chunk ID
            text: Text content
            embedding: Vector embedding
            metadata: Additional metadata
            
        Returns:
            Result of the operation
        """
        logger.info(f"Storing vector: {chunk_id} for document: {doc_id}")
        
        try:
            # Use MCP server if endpoint not provided directly
            if not self.api_endpoint:
                return await self._call_mcp_tool("create_vector", {
                    "tenantId": tenant_id,
                    "docId": doc_id,
                    "chunkId": chunk_id,
                    "text": text,
                    "embedding": embedding,
                    "metadata": metadata or {}
                })
                
            # Direct API call to Astra
            headers = {
                "Content-Type": "application/json",
                "X-Cassandra-Token": self.token
            }
            
            url = f"{self.api_endpoint}/api/rest/v2/keyspaces/{self.keyspace}/vectors"
            
            data = {
                "tenant_id": tenant_id,
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 201:
                        return {
                            "success": True,
                            "chunk_id": chunk_id
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error storing vector: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def create_edge(self, tenant_id: str, from_id: str, to_id: str, 
                         relation_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a graph edge in Astra DB.
        
        Args:
            tenant_id: Tenant ID
            from_id: ID of the source node
            to_id: ID of the target node
            relation_type: Type of relationship
            properties: Additional properties
            
        Returns:
            The created edge
        """
        logger.info(f"Creating edge: {relation_type} from {from_id} to {to_id}")
        
        try:
            # Use MCP server if endpoint not provided directly
            if not self.api_endpoint:
                return await self._call_mcp_tool("create_edge", {
                    "tenantId": tenant_id,
                    "fromId": from_id,
                    "toId": to_id,
                    "relationType": relation_type,
                    "properties": properties or {}
                })
                
            # Direct API call to Astra
            headers = {
                "Content-Type": "application/json",
                "X-Cassandra-Token": self.token
            }
            
            url = f"{self.api_endpoint}/api/rest/v2/keyspaces/{self.keyspace}/graph_edges"
            
            data = {
                "tenant_id": tenant_id,
                "from_id": from_id,
                "to_id": to_id,
                "relation_type": relation_type,
                "weight": 1.0,  # Default weight
                "properties": properties or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 201:
                        return {
                            "from": from_id,
                            "to": to_id,
                            "type": relation_type,
                            "properties": properties or {}
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error creating edge: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Error creating edge: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool response
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.mcp_server_url}/mcp/tools/{tool_name}"
            
            try:
                async with session.post(url, json=arguments) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("result", {})
                    else:
                        error_text = await response.text()
                        logger.error(f"Error calling MCP tool {tool_name}: {response.status} - {error_text}")
                        raise Exception(f"MCP tool {tool_name} failed: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error calling MCP tool {tool_name}: {str(e)}")
                raise
