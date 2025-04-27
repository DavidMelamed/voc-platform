"""Real Pulsar client implementation for the VOC Platform.

This module provides a fully functional client for interacting with Astra Streaming (Pulsar).
It can be used across all agents for consistent messaging.
"""

import os
import json
import asyncio
import pulsar
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable


class PulsarClient:
    """Client for interacting with Astra Streaming (Pulsar)."""
    
    def __init__(self):
        """Initialize the Pulsar client with environment variables."""
        self.tenant = os.getenv("ASTRA_STREAMING_TENANT", "default")
        self.namespace = os.getenv("ASTRA_STREAMING_NAMESPACE", "default")
        self.token = os.getenv("ASTRA_STREAMING_TOKEN", "")
        self.broker_url = os.getenv("ASTRA_STREAMING_BROKER_URL", "")
        
        if not self.broker_url:
            raise ValueError("ASTRA_STREAMING_BROKER_URL not set in environment")
            
        if not self.token:
            raise ValueError("ASTRA_STREAMING_TOKEN not set in environment")
        
        # Real Pulsar client
        self.client = None
        self.producers = {}
        self.consumers = {}
        
        print(f"Initialized Pulsar client for tenant {self.tenant}")
    
    async def connect(self):
        """Connect to Astra Streaming."""
        try:
            # Using Pulsar's Python client
            self.client = pulsar.Client(
                service_url=self.broker_url,
                authentication=pulsar.AuthenticationToken(self.token)
            )
            print(f"Connected to Astra Streaming at {self.broker_url}")
            return True
        except Exception as e:
            print(f"Error connecting to Astra Streaming: {str(e)}")
            raise
    
    async def close(self):
        """Close the connection to Astra Streaming."""
        try:
            # Close all producers
            for producer in self.producers.values():
                producer.close()
            
            # Close all consumers
            for consumer in self.consumers.values():
                consumer.close()
            
            # Close the client
            if self.client:
                self.client.close()
                self.client = None
            
            print("Closed Pulsar client connection")
            return True
        except Exception as e:
            print(f"Error closing Pulsar connection: {str(e)}")
            raise
    
    async def create_producer(self, topic: str):
        """Create a producer for a topic."""
        if not self.client:
            await self.connect()
        
        try:
            full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
            producer = self.client.create_producer(full_topic)
            self.producers[topic] = producer
            print(f"Created producer for topic {full_topic}")
            return {"topic": full_topic, "producer": producer}
        except Exception as e:
            print(f"Error creating producer for topic {topic}: {str(e)}")
            raise
    
    async def create_consumer(self, topic: str, subscription_name: str):
        """Create a consumer for a topic."""
        if not self.client:
            await self.connect()
        
        try:
            full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
            consumer = self.client.subscribe(
                topic=full_topic,
                subscription_name=subscription_name,
                consumer_type=pulsar.ConsumerType.Shared
            )
            self.consumers[f"{topic}-{subscription_name}"] = consumer
            print(f"Created consumer for topic {full_topic} with subscription {subscription_name}")
            return {"topic": full_topic, "subscription": subscription_name, "consumer": consumer}
        except Exception as e:
            print(f"Error creating consumer for topic {topic}: {str(e)}")
            raise
    
    async def send_message(self, topic: str, content: Union[str, Dict, bytes], properties: Dict = None):
        """Send a message to a topic."""
        # Ensure producer exists
        if topic not in self.producers:
            await self.create_producer(topic)
        
        try:
            # Convert content to bytes if it's not already
            if isinstance(content, dict):
                content = json.dumps(content).encode('utf-8')
            elif isinstance(content, str):
                content = content.encode('utf-8')
            
            # Send the message with properties if provided
            if properties:
                message_id = self.producers[topic].send(content, properties=properties)
            else:
                message_id = self.producers[topic].send(content)
            
            full_topic = f"persistent://{self.tenant}/{self.namespace}/{topic}"
            print(f"Sent message to topic {full_topic}, message_id: {message_id}")
            
            return message_id
        except Exception as e:
            print(f"Error sending message to topic {topic}: {str(e)}")
            raise
    
    async def receive_message(self, topic: str, subscription_name: str, timeout_ms: int = 5000):
        """Receive a message from a topic."""
        consumer_key = f"{topic}-{subscription_name}"
        
        # Ensure consumer exists
        if consumer_key not in self.consumers:
            await self.create_consumer(topic, subscription_name)
        
        try:
            # Receive message with timeout
            message = self.consumers[consumer_key].receive(timeout_millis=timeout_ms)
            return message
        except Exception as e:
            if "Pulsar error: TimeOut" in str(e):
                # This is normal for no messages, return None
                return None
            print(f"Error receiving message from topic {topic}: {str(e)}")
            raise
    
    async def acknowledge_message(self, topic: str, subscription_name: str, message):
        """Acknowledge that a message has been processed."""
        consumer_key = f"{topic}-{subscription_name}"
        
        # Ensure the consumer exists
        if consumer_key not in self.consumers:
            print(f"Warning: No consumer found for {consumer_key}, cannot acknowledge message")
            return False
        
        try:
            # Acknowledge the message
            self.consumers[consumer_key].acknowledge(message)
            return True
        except Exception as e:
            print(f"Error acknowledging message: {str(e)}")
            raise
    
    async def subscribe_and_process(self, topic: str, subscription_name: str, 
                                   callback: Callable, ack_messages: bool = True,
                                   poll_interval: float = 1.0):
        """Subscribe to a topic and process messages as they arrive.
        
        Args:
            topic: The topic to subscribe to
            subscription_name: The subscription name
            callback: A callback function that takes a message as input
            ack_messages: Whether to acknowledge messages after processing
            poll_interval: How often to poll for new messages (in seconds)
        """
        try:
            # Ensure consumer exists
            consumer_key = f"{topic}-{subscription_name}"
            if consumer_key not in self.consumers:
                await self.create_consumer(topic, subscription_name)
            
            # Start the processing loop
            while True:
                try:
                    message = self.consumers[consumer_key].receive(timeout_millis=int(poll_interval * 1000))
                    if message:
                        # Extract content
                        content = message.data()
                        properties = message.properties()
                        
                        # Process the message with the callback
                        await callback(content, properties, message)
                        
                        # Acknowledge the message if required
                        if ack_messages:
                            self.consumers[consumer_key].acknowledge(message)
                except Exception as e:
                    if "Pulsar error: TimeOut" not in str(e):
                        print(f"Error processing message: {str(e)}")
                    # Continue the loop even if there's an error
                    await asyncio.sleep(poll_interval)
        except Exception as e:
            print(f"Error in subscribe_and_process: {str(e)}")
            raise
