"""
Langfuse Python integration for the Voice-of-Customer & Brand-Intel Platform.

This module provides utilities for integrating Langfuse observability
with the Python-based agents in the platform.
"""

import os
import time
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from langfuse.utils import get_llm_usage

class LangfuseMonitor:
    """Langfuse integration for monitoring agent operations and LLM calls."""
    
    def __init__(self, tenant_id: str = None):
        """
        Initialize Langfuse monitoring.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant deployments
        """
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
        
        self.tenant_id = tenant_id
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def create_trace(
        self, 
        name: str, 
        metadata: Dict[str, Any] = None, 
        tags: List[str] = None
    ) -> Any:
        """
        Create a new trace for tracking a full agent operation.
        
        Args:
            name: Name of the trace
            metadata: Additional context for the trace
            tags: List of tags for filtering
            
        Returns:
            A trace object
        """
        metadata = metadata or {}
        if self.tenant_id:
            metadata["tenant_id"] = self.tenant_id
            
        metadata["environment"] = self.environment
        
        trace = self.langfuse.trace(
            name=name,
            metadata=metadata,
            tags=tags or [],
            user_id=self.tenant_id
        )
        
        return trace
        
    def create_span(
        self,
        trace_id: str,
        name: str,
        metadata: Dict[str, Any] = None,
        parent_id: str = None
    ) -> Any:
        """
        Create a span for measuring duration of an operation.
        
        Args:
            trace_id: The ID of the parent trace
            name: Name of the span
            metadata: Additional context
            parent_id: Optional parent span ID for nesting
            
        Returns:
            A span object
        """
        metadata = metadata or {}
        
        span = self.langfuse.span(
            trace_id=trace_id,
            name=name,
            metadata=metadata,
            parent_id=parent_id
        )
        
        return span
        
    def end_span(
        self,
        span,
        status: str = "success",
        metadata: Dict[str, Any] = None
    ):
        """
        End a span and record its status.
        
        Args:
            span: The span to end
            status: Outcome of the operation (success, error)
            metadata: Additional result information
        """
        span.end(
            status=status,
            metadata=metadata or {}
        )
        
    def log_llm(
        self,
        trace_id: str,
        name: str,
        model: str,
        prompt: Union[str, List[Dict[str, str]]],
        completion: str,
        metadata: Dict[str, Any] = None,
        parent_id: str = None
    ) -> Any:
        """
        Log an LLM generation.
        
        Args:
            trace_id: The ID of the parent trace
            name: Name of this generation
            model: LLM model used
            prompt: Prompt or messages sent to the LLM
            completion: LLM response
            metadata: Additional context
            parent_id: Optional parent span ID
            
        Returns:
            The generation object
        """
        metadata = metadata or {}
        
        # Calculate token usage if possible
        input_tokens = 0
        output_tokens = 0
        try:
            # Attempt to estimate usage
            usage = get_llm_usage(model, prompt, completion)
            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]
        except:
            # If estimation fails, default to 0
            pass
            
        generation = self.langfuse.generation(
            trace_id=trace_id,
            name=name,
            model=model,
            prompt=prompt,
            completion=completion,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata,
            parent_id=parent_id
        )
        
        return generation
        
    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str = None
    ):
        """
        Add a score to evaluate quality of a trace.
        
        Args:
            trace_id: The ID of the trace to score
            name: Name of the score
            value: Score value (0.0 to 1.0)
            comment: Optional explanation of the score
        """
        self.langfuse.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment
        )
        
    def log_event(
        self,
        trace_id: str,
        name: str,
        level: str = "info",
        metadata: Dict[str, Any] = None,
        parent_id: str = None
    ):
        """
        Log an event or observation.
        
        Args:
            trace_id: The ID of the parent trace
            name: Name of the event
            level: Log level (info, warning, error)
            metadata: Additional context
            parent_id: Optional parent span ID
        """
        metadata = metadata or {}
        metadata["level"] = level
        
        self.langfuse.observation(
            trace_id=trace_id,
            name=name,
            metadata=metadata,
            parent_id=parent_id
        )

# Function decorators for easy monitoring

def trace_agent_task(task_name: str, agent_type: str):
    """
    Decorator to trace an agent task.
    
    Args:
        task_name: Name of the task
        agent_type: Type of agent (coordinator, scraper, etc.)
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @langfuse_context
        async def wrapper(self, *args, **kwargs):
            tenant_id = getattr(self, "tenant_id", None)
            monitor = LangfuseMonitor(tenant_id)
            
            trace = monitor.create_trace(
                name=task_name,
                metadata={"agent_type": agent_type},
                tags=[agent_type, task_name]
            )
            
            # Set trace context for nested spans
            with langfuse_context(trace_id=trace.id):
                try:
                    start_time = time.time()
                    result = await func(self, *args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log success
                    monitor.log_event(
                        trace_id=trace.id,
                        name=f"{task_name}_complete",
                        metadata={
                            "execution_time": execution_time,
                            "success": True
                        }
                    )
                    
                    # Score based on execution time (example metric)
                    # Faster is better, with reasonable bounds
                    if execution_time < 60:
                        speed_score = 1.0
                    elif execution_time < 300:
                        speed_score = 0.8
                    else:
                        speed_score = 0.6
                        
                    monitor.score(
                        trace_id=trace.id,
                        name="execution_speed",
                        value=speed_score
                    )
                    
                    return result
                    
                except Exception as e:
                    # Log failure
                    monitor.log_event(
                        trace_id=trace.id,
                        name=f"{task_name}_error",
                        level="error",
                        metadata={
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    raise
                    
        return wrapper
    return decorator

def trace_llm_call(model_name: str, generation_name: str):
    """
    Decorator to trace an LLM call.
    
    Args:
        model_name: Name of the LLM model
        generation_name: Name of this generation type
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @observe(handler="langfuse")
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = await func(self, *args, **kwargs)
            end_time = time.time()
            
            # Access the current trace context
            if hasattr(wrapper, "current_trace_id"):
                tenant_id = getattr(self, "tenant_id", None)
                monitor = LangfuseMonitor(tenant_id)
                
                # Extract prompt and completion from args/result
                # This is a simplified example - adjust based on your LLM function signature
                prompt = args[0] if args else kwargs.get("prompt", "")
                completion = result.get("content", str(result))
                
                monitor.log_llm(
                    trace_id=wrapper.current_trace_id,
                    name=generation_name,
                    model=model_name,
                    prompt=prompt,
                    completion=completion,
                    metadata={
                        "execution_time": end_time - start_time
                    }
                )
                
            return result
            
        return wrapper
    return decorator
