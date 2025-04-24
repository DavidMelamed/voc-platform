"""
Coordinator Agent for Voice-of-Customer & Brand-Intel Platform.

This agent is responsible for:
1. Pulling top-priority jobs from Pulsar
2. Dispatching Scraper Agent
3. Calling Tagger Agent
4. Writing graph edges
5. Emitting events
6. Enforcing stop conditions & budget caps
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from pulsar_client import PulsarClient
from mcp_client import McpClient
from budget_tracker import BudgetTracker

# Load environment variables
load_dotenv()

# Initialize clients
pulsar_client = PulsarClient()
mcp_client = McpClient()
budget_tracker = BudgetTracker()

# Configuration
TENANT_ID = os.getenv("TENANT_ID", "default")
TENANT_NAME = os.getenv("TENANT_NAME", "Default Tenant")
STOP_ON_UNKNOWN_DOMAINS = os.getenv("COORDINATOR_STOP_ON_UNKNOWN_DOMAINS", "true").lower() == "true"
BUDGET_CAP_USD = float(os.getenv("COORDINATOR_BUDGET_CAP_USD", "100"))
HUMAN_APPROVAL_EMAIL = os.getenv("COORDINATOR_HUMAN_APPROVAL_EMAIL", "")

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")

# State definition
class AgentState(BaseModel):
    """State for the coordinator agent workflow."""
    job: Dict = Field(default_factory=dict, description="Current job being processed")
    scrape_results: Optional[Dict] = Field(default=None, description="Results from the scraper")
    tagging_results: Optional[Dict] = Field(default=None, description="Results from the tagger")
    graph_results: Optional[Dict] = Field(default=None, description="Results from graph operations")
    stop_conditions: List[str] = Field(default_factory=list, description="Active stop conditions")
    budget_used: float = Field(default=0.0, description="Budget used for current job in USD")
    need_human_approval: bool = Field(default=False, description="Whether human approval is needed")
    human_approval_reason: Optional[str] = Field(default=None, description="Reason for human approval")
    errors: List[Dict] = Field(default_factory=list, description="Errors encountered during processing")
    status: str = Field(default="pending", description="Current status of the job")

# Node functions
async def get_next_job(state: AgentState) -> AgentState:
    """Pull the next highest-priority job from the Pulsar queue."""
    try:
        # Get the next job from Pulsar
        message = await pulsar_client.receive_message("scrape.jobs")
        
        if not message:
            state.status = "no_jobs"
            return state
            
        job_data = json.loads(message.data().decode("utf-8"))
        
        # Acknowledge the message
        await pulsar_client.acknowledge(message)
        
        # Update state with job data
        state.job = job_data
        state.status = "job_received"
        
        # Reset other state fields for new job
        state.scrape_results = None
        state.tagging_results = None
        state.graph_results = None
        state.stop_conditions = []
        state.budget_used = 0.0
        state.need_human_approval = False
        state.human_approval_reason = None
        state.errors = []
        
        # Log job start
        print(f"Starting job: {job_data.get('id', 'unknown')}")
        
    except Exception as e:
        state.errors.append({
            "step": "get_next_job",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        state.status = "error"
        
    return state

async def check_stop_conditions(state: AgentState) -> AgentState:
    """Check if any stop conditions are met."""
    # Clear previous stop conditions
    state.stop_conditions = []
    
    # Check budget cap
    if state.budget_used >= BUDGET_CAP_USD:
        state.stop_conditions.append("budget_cap_exceeded")
    
    # Check for unknown domains
    if STOP_ON_UNKNOWN_DOMAINS and state.job.get("domain_verified", False) is False:
        state.stop_conditions.append("unknown_domain")
    
    # Set need_human_approval if any stop conditions are met
    if state.stop_conditions:
        state.need_human_approval = True
        state.human_approval_reason = ", ".join(state.stop_conditions)
        state.status = "awaiting_approval"
    
    return state

async def request_human_approval(state: AgentState) -> AgentState:
    """Request human approval for the job."""
    if not state.need_human_approval:
        return state
        
    # In a real implementation, this would send an email or notification
    print(f"Human approval needed for job {state.job.get('id', 'unknown')}")
    print(f"Reason: {state.human_approval_reason}")
    print(f"Sending approval request to: {HUMAN_APPROVAL_EMAIL}")
    
    # For now, we'll auto-approve for demonstration
    # In a real implementation, this would wait for approval
    state.need_human_approval = False
    state.status = "approved"
    
    return state

async def dispatch_scraper(state: AgentState) -> AgentState:
    """Dispatch the scraper agent to collect data."""
    try:
        job_id = state.job.get("id", str(uuid.uuid4()))
        source_type = state.job.get("source_type", "unknown")
        url = state.job.get("url")
        keywords = state.job.get("keywords", [])
        
        # Prepare scraper job message
        scraper_job = {
            "job_id": job_id,
            "tenant_id": TENANT_ID,
            "source_type": source_type,
            "url": url,
            "keywords": keywords,
            "timestamp": datetime.now().isoformat(),
            "priority": state.job.get("priority", "medium")
        }
        
        # Send to scraper queue
        await pulsar_client.send_message("scrape.results", json.dumps(scraper_job).encode("utf-8"))
        
        # In a real implementation, we might wait for a response here
        # For now, we'll simulate a response
        
        scrape_results = {
            "job_id": job_id,
            "tenant_id": TENANT_ID,
            "source_type": source_type,
            "url": url,
            "content": f"Simulated content for {url or keywords}",
            "metadata": {
                "source_type": source_type,
                "scrape_time": datetime.now().isoformat(),
                "success": True
            },
            "status": "completed"
        }
        
        # Update state
        state.scrape_results = scrape_results
        state.status = "scraping_completed"
        
        # Track budget
        cost_estimate = 0.02  # Example cost in USD
        state.budget_used += cost_estimate
        budget_tracker.add_cost(job_id, "scraping", cost_estimate)
        
    except Exception as e:
        state.errors.append({
            "step": "dispatch_scraper",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        state.status = "error"
        
    return state

async def dispatch_tagger(state: AgentState) -> AgentState:
    """Dispatch the tagger agent to process and enrich data."""
    try:
        if not state.scrape_results:
            state.errors.append({
                "step": "dispatch_tagger",
                "error": "No scrape results available",
                "timestamp": datetime.now().isoformat()
            })
            state.status = "error"
            return state
            
        job_id = state.job.get("id", state.scrape_results.get("job_id"))
        
        # Prepare tagger job message
        tagger_job = {
            "job_id": job_id,
            "tenant_id": TENANT_ID,
            "source_type": state.scrape_results.get("source_type"),
            "content": state.scrape_results.get("content"),
            "metadata": state.scrape_results.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to tagger
        await pulsar_client.send_message("tag.complete", json.dumps(tagger_job).encode("utf-8"))
        
        # Simulate tagger results
        tagging_results = {
            "job_id": job_id,
            "tenant_id": TENANT_ID,
            "doc_id": str(uuid.uuid4()),
            "sentiment": "positive",
            "topics": ["product", "service", "quality"],
            "urgency": False,
            "source_type": state.scrape_results.get("source_type"),
            "embedding_id": str(uuid.uuid4()),
            "entities": [
                {"type": "Brand", "name": "Example Brand", "id": str(uuid.uuid4())},
                {"type": "Topic", "name": "Quality", "id": str(uuid.uuid4())}
            ],
            "status": "completed"
        }
        
        # Update state
        state.tagging_results = tagging_results
        state.status = "tagging_completed"
        
        # Track budget
        cost_estimate = 0.05  # Example cost in USD
        state.budget_used += cost_estimate
        budget_tracker.add_cost(job_id, "tagging", cost_estimate)
        
    except Exception as e:
        state.errors.append({
            "step": "dispatch_tagger",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        state.status = "error"
        
    return state

async def create_graph_edges(state: AgentState) -> AgentState:
    """Create graph edges from the tagged data."""
    try:
        if not state.tagging_results:
            state.errors.append({
                "step": "create_graph_edges",
                "error": "No tagging results available",
                "timestamp": datetime.now().isoformat()
            })
            state.status = "error"
            return state
            
        # Extract entities and create edges
        doc_id = state.tagging_results.get("doc_id")
        entities = state.tagging_results.get("entities", [])
        edges = []
        
        # Create edges between document and entities
        for entity in entities:
            edge = {
                "from_id": doc_id,
                "to_id": entity.get("id"),
                "relation_type": "MENTIONS" if entity.get("type") == "Topic" else "ABOUT",
                "properties": {
                    "confidence": 0.9,  # Example confidence score
                    "created_at": datetime.now().isoformat()
                }
            }
            edges.append(edge)
            
        # Simulate creating edges in the database
        # In a real implementation, this would use the MCP client
        
        # Update state
        state.graph_results = {
            "edges_created": len(edges),
            "edges": edges,
            "status": "completed"
        }
        state.status = "graph_completed"
        
    except Exception as e:
        state.errors.append({
            "step": "create_graph_edges",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        state.status = "error"
        
    return state

async def emit_events(state: AgentState) -> AgentState:
    """Emit events for downstream processing."""
    try:
        if not state.tagging_results or not state.graph_results:
            state.errors.append({
                "step": "emit_events",
                "error": "Missing required results",
                "timestamp": datetime.now().isoformat()
            })
            state.status = "error"
            return state
            
        # Create event message
        event = {
            "job_id": state.job.get("id"),
            "tenant_id": TENANT_ID,
            "doc_id": state.tagging_results.get("doc_id"),
            "process_time": datetime.now().isoformat(),
            "sentiment": state.tagging_results.get("sentiment"),
            "topics": state.tagging_results.get("topics"),
            "urgency": state.tagging_results.get("urgency"),
            "source_type": state.tagging_results.get("source_type"),
            "edges_created": state.graph_results.get("edges_created"),
            "status": "completed"
        }
        
        # Emit the event
        await pulsar_client.send_message("analysis.jobs", json.dumps(event).encode("utf-8"))
        
        # Update state
        state.status = "completed"
        
    except Exception as e:
        state.errors.append({
            "step": "emit_events",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        state.status = "error"
        
    return state

async def handle_error(state: AgentState) -> AgentState:
    """Handle errors in the workflow."""
    # Log the error
    print(f"Error processing job {state.job.get('id', 'unknown')}")
    for error in state.errors:
        print(f"  Step: {error['step']}, Error: {error['error']}")
    
    # In a real implementation, this might retry or send to a dead letter queue
    
    # Mark the job as failed
    state.status = "failed"
    
    return state

# Router function for conditional branching
def router(state: AgentState) -> str:
    """Route to the next step based on the current state."""
    # Check for errors
    if state.errors:
        return "handle_error"
        
    # Route based on status
    if state.status == "no_jobs":
        return END
    
    if state.status == "job_received":
        return "check_stop_conditions"
        
    if state.status == "awaiting_approval":
        return "request_human_approval"
        
    if state.status in ["approved", "job_received"]:
        return "dispatch_scraper"
        
    if state.status == "scraping_completed":
        return "dispatch_tagger"
        
    if state.status == "tagging_completed":
        return "create_graph_edges"
        
    if state.status == "graph_completed":
        return "emit_events"
        
    if state.status == "completed":
        return "get_next_job"
        
    # Default to end
    return END

# Create the graph
def create_workflow() -> StateGraph:
    """Create the coordinator workflow graph."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("get_next_job", get_next_job)
    workflow.add_node("check_stop_conditions", check_stop_conditions)
    workflow.add_node("request_human_approval", request_human_approval)
    workflow.add_node("dispatch_scraper", dispatch_scraper)
    workflow.add_node("dispatch_tagger", dispatch_tagger)
    workflow.add_node("create_graph_edges", create_graph_edges)
    workflow.add_node("emit_events", emit_events)
    workflow.add_node("handle_error", handle_error)
    
    # Set the entry point
    workflow.set_entry_point("get_next_job")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "get_next_job",
        router
    )
    
    workflow.add_conditional_edges(
        "check_stop_conditions",
        router
    )
    
    workflow.add_conditional_edges(
        "request_human_approval",
        router
    )
    
    workflow.add_conditional_edges(
        "dispatch_scraper",
        router
    )
    
    workflow.add_conditional_edges(
        "dispatch_tagger",
        router
    )
    
    workflow.add_conditional_edges(
        "create_graph_edges",
        router
    )
    
    workflow.add_conditional_edges(
        "emit_events",
        router
    )
    
    workflow.add_edge("handle_error", END)
    
    return workflow

# Instantiate the workflow
coordinator_workflow = create_workflow()

# Compile the workflow into a runnable
coordinator_app = coordinator_workflow.compile()

if __name__ == "__main__":
    # Run the workflow
    coordinator_app.invoke({"status": "pending"})
