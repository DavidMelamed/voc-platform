"""
Pulsar client for the Scraper Agent.

This module provides a client for interacting with Astra Streaming (Pulsar)
for the Scraper Agent.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# This is a simplified version of the same client used in the Coordinator Agent
# In a real implementation, this would be a shared library

class PulsarClient:
    """Client for interacting with Astra Streaming (Pulsar)."""
    
    def __init__(self):
        """Initialize the Pulsar client with environment variables."""
        self.tenant = os.getenv("ASTRA_STREAMING_TENANT", "default")
        self.namespace = os.getenv("ASTRA_STREAMING_NAMESPACE", "voc_platform")
        self.token = os.getenv("ASTRA_STREAMING_TOKEN", "")
        self.broker_url = f"pulsar+ssl://{self.tenant}.streaming.datastax.com:6651"
        
        # Mock message storage for demo purposes
        self.topics = {
            "scrape.jobs": [],
            "scrape.results": [],
            "tag.complete": [],
            "analysis.jobs": [],
            "analysis.done": []
        }
        
        print(f"Initialized Pulsar client for tenant {self.tenant}")
    
    async def connect(self):
        """Connect to Astra Streaming."""
        # In a real implementation, this would establish a connection
        print(f"Connected to Astra Streaming at {self.broker_url}")
        return True
        
    async def close(self):
        """Close the connection to Astra Streaming."""
        # In a real implementation, this would close connections
        print("Closed Pulsar client connection")
        return True
        
    async def create_producer(self, topic: str):
        """Create a producer for a topic."""
        # In a real implementation, this would create a Pulsar producer
        full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
        print(f"Created producer for topic {full_topic}")
        return {"topic": full_topic}
        
    async def create_consumer(self, topic: str, subscription_name: str):
        """Create a consumer for a topic."""
        # In a real implementation, this would create a Pulsar consumer
        full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
        print(f"Created consumer for topic {full_topic} with subscription {subscription_name}")
        return {"topic": full_topic, "subscription": subscription_name}
        
    async def send_message(self, topic: str, content: Union[str, bytes], properties: Dict = None):
        """Send a message to a topic."""
        # In a real implementation, this would use a Pulsar producer
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Mock implementation - store message in our topic storage
        message = {
            "content": content,
            "properties": properties or {},
            "timestamp": datetime.now().isoformat(),
            "message_id": f"mock-msg-{len(self.topics[topic])}"
        }
        
        self.topics[topic].append(message)
        
        full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
        print(f"Sent message to topic {full_topic}")
        
        return message["message_id"]
        
    async def receive_message(self, topic: str, timeout_ms: int = 5000):
        """Receive a message from a topic."""
        # In a real implementation, this would use a Pulsar consumer
        
        # Mock implementation - get first message from topic if available
        if self.topics[topic]:
            message = self.topics[topic][0]
            
            # Create a mock message object
            class MockMessage:
                def __init__(self, data, msg_id, properties):
                    self._data = data
                    self._msg_id = msg_id
                    self._properties = properties
                
                def data(self):
                    return self._data
                    
                def message_id(self):
                    return self._msg_id
                    
                def properties(self):
                    return self._properties
            
            return MockMessage(
                message["content"],
                message["message_id"],
                message["properties"]
            )
        
        return None
        
    async def acknowledge(self, message):
        """Acknowledge a message."""
        # In a real implementation, this would acknowledge the message
        
        # Mock implementation - remove message from our topic storage
        for topic, messages in self.topics.items():
            for i, msg in enumerate(messages):
                if msg["message_id"] == message.message_id():
                    self.topics[topic].pop(i)
                    print(f"Acknowledged message {message.message_id()}")
                    return True
        
        return False
