"""
MCP client for the Voice-of-Customer & Brand-Intel Platform.

This module provides a client for interacting with the MCP server.
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional, Any, Union

class McpClient:
    """Client for interacting with the MCP server."""
    
    def __init__(self):
        """Initialize the MCP client with environment variables."""
        self.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.tenant_id = os.getenv("TENANT_ID", "default")
        
        print(f"Initialized MCP client for {self.server_url}")
    
    async def vector_search(self, query: str, limit: int = 10, filter: Dict = None) -> List[Dict]:
        """Search for documents using vector similarity."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/vector-search"
            payload = {
                "query": query,
                "limit": limit,
                "filter": filter or {}
            }
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Vector search failed: {response.status} - {error_text}")
    
    async def hybrid_search(self, query: str, limit: int = 10, 
                           vector_weight: float = 0.5, filter: Dict = None) -> List[Dict]:
        """Search for documents using both keyword and semantic similarity."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/hybrid-search"
            payload = {
                "query": query,
                "limit": limit,
                "vectorWeight": vector_weight,
                "filter": filter or {}
            }
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Hybrid search failed: {response.status} - {error_text}")
    
    async def get_raw_doc(self, doc_id: str) -> Dict:
        """Retrieve a raw document by ID."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/get-raw-doc"
            payload = {
                "docId": doc_id
            }
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {})
                else:
                    error_text = await response.text()
                    raise Exception(f"Get raw document failed: {response.status} - {error_text}")
    
    async def graph_query(self, from_type: str, relation: str, to_type: str, 
                         from_id: str = None, to_id: str = None, limit: int = 10) -> List[Dict]:
        """Query the knowledge graph."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/graph-query"
            payload = {
                "fromType": from_type,
                "relation": relation,
                "toType": to_type,
                "limit": limit
            }
            
            if from_id:
                payload["fromId"] = from_id
                
            if to_id:
                payload["toId"] = to_id
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Graph query failed: {response.status} - {error_text}")
    
    async def create_edge(self, from_id: str, to_id: str, relation_type: str, 
                         weight: float = 1.0, properties: Dict = None) -> Dict:
        """Create a graph edge."""
        # This is a custom method - we'll implement this directly via Astra DB
        # as it's not exposed as an MCP tool
        
        # In a real implementation, this would interact with the database
        # For now, we'll just return a mock result
        edge = {
            "from": from_id,
            "to": to_id,
            "type": relation_type,
            "weight": weight,
            "properties": properties or {},
            "created": True
        }
        
        print(f"Created edge from {from_id} to {to_id} with type {relation_type}")
        
        return edge
    
    async def get_insight(self, insight_id: str) -> Dict:
        """Get an insight by ID."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/get-insight"
            payload = {
                "insightId": insight_id
            }
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {})
                else:
                    error_text = await response.text()
                    raise Exception(f"Get insight failed: {response.status} - {error_text}")
    
    async def list_insights(self, filter: Dict = None, limit: int = 10, last_key: str = None) -> Dict:
        """List insights with optional filtering."""
        async with aiohttp.ClientSession() as session:
            tool_url = f"{self.server_url}/mcp/tools/list-insights"
            payload = {
                "filter": filter or {},
                "limit": limit
            }
            
            if last_key:
                payload["lastKey"] = last_key
            
            async with session.post(tool_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {"insights": [], "pagination": {}})
                else:
                    error_text = await response.text()
                    raise Exception(f"List insights failed: {response.status} - {error_text}")
