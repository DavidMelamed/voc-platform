"""
Real Pulsar client for the Tagger Agent.

This module imports the real Pulsar client implementation from the common module.
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union, Callable

# Add the common module to the path
common_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'common')
sys.path.append(common_path)

# Import the real Pulsar client implementation
try:
    from pulsar_client import PulsarClient as RealPulsarClient
    
    # Use the real implementation
    PulsarClient = RealPulsarClient
    print("Using real Pulsar client implementation from common module")
except ImportError as e:
    print(f"Warning: Failed to import real Pulsar client: {str(e)}")
    # If the import fails, provide a minimal implementation that logs the failure
    class PulsarClient:
        """Fallback Pulsar client that logs errors."""
        
        def __init__(self):
            """Initialize with a warning about the missing real implementation."""
            print("ERROR: Using fallback Pulsar client - no real functionality available!")
            print("Please ensure the common/pulsar_client.py module is available")
            self.tenant = os.getenv("ASTRA_STREAMING_TENANT", "default")
        
        async def connect(self):
            print("ERROR: Cannot connect with fallback Pulsar client")
            return False
            
        async def close(self):
            print("ERROR: No real connection to close")
            return False
        
        async def create_producer(self, topic):
            print(f"ERROR: Cannot create producer for topic {topic} - no real implementation")
            return None
        
        async def create_consumer(self, topic, subscription_name):
            print(f"ERROR: Cannot create consumer for topic {topic} - no real implementation")
            return None
        
        async def send_message(self, topic, content, properties=None):
            print(f"ERROR: Cannot send message to topic {topic} - no real implementation")
            return None
        
        async def receive_message(self, topic, subscription_name, timeout_ms=5000):
            print(f"ERROR: Cannot receive message from topic {topic} - no real implementation")
            return None
            
        async def acknowledge_message(self, topic, subscription_name, message):
            print(f"ERROR: Cannot acknowledge message - no real implementation")
            return False
        
        async def subscribe_and_process(self, topic, subscription_name, callback, ack_messages=True, poll_interval=1.0):
            print(f"ERROR: Cannot subscribe to topic {topic} - no real implementation")
            return None
        

