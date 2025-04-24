"""
Budget tracker for the Voice-of-Customer & Brand-Intel Platform.

This module provides a utility for tracking costs and enforcing budget caps.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

class BudgetTracker:
    """Utility for tracking costs and enforcing budget caps."""
    
    def __init__(self):
        """Initialize the budget tracker."""
        self.budget_cap = float(os.getenv("COORDINATOR_BUDGET_CAP_USD", "100"))
        
        # Tracking structures
        self.total_cost = 0.0
        self.jobs = {}  # job_id -> {total_cost, operations}
        self.operations_cost = {
            "scraping": 0.0,
            "tagging": 0.0,
            "embedding": 0.0,
            "analysis": 0.0,
            "other": 0.0
        }
        
        print(f"Initialized budget tracker with cap: ${self.budget_cap:.2f}")
    
    def add_cost(self, job_id: str, operation_type: str, cost: float) -> float:
        """
        Add a cost for an operation.
        
        Args:
            job_id: ID of the job
            operation_type: Type of operation (scraping, tagging, etc.)
            cost: Cost in USD
            
        Returns:
            Updated total cost for the job
        """
        # Ensure operation type is valid
        if operation_type not in self.operations_cost:
            operation_type = "other"
            
        # Initialize job if not exists
        if job_id not in self.jobs:
            self.jobs[job_id] = {
                "total_cost": 0.0,
                "operations": [],
                "start_time": datetime.now().isoformat()
            }
            
        # Add the cost
        self.total_cost += cost
        self.operations_cost[operation_type] += cost
        
        # Update job costs
        self.jobs[job_id]["total_cost"] += cost
        self.jobs[job_id]["operations"].append({
            "type": operation_type,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"Added ${cost:.4f} for {operation_type} to job {job_id}. "
              f"Job total: ${self.jobs[job_id]['total_cost']:.4f}, "
              f"Overall total: ${self.total_cost:.4f}")
              
        return self.jobs[job_id]["total_cost"]
    
    def get_job_cost(self, job_id: str) -> float:
        """Get the total cost for a job."""
        if job_id in self.jobs:
            return self.jobs[job_id]["total_cost"]
        return 0.0
    
    def get_total_cost(self) -> float:
        """Get the total cost across all jobs."""
        return self.total_cost
    
    def would_exceed_budget(self, cost: float) -> bool:
        """Check if adding a cost would exceed the budget cap."""
        return (self.total_cost + cost) > self.budget_cap
    
    def get_job_details(self, job_id: str) -> Dict:
        """Get detailed information about a job's costs."""
        if job_id not in self.jobs:
            return {
                "job_id": job_id,
                "total_cost": 0.0,
                "operations": [],
                "start_time": None,
                "exists": False
            }
            
        job_data = self.jobs[job_id].copy()
        job_data["job_id"] = job_id
        job_data["exists"] = True
        
        # Calculate operation type totals
        operation_totals = {}
        for op in job_data["operations"]:
            op_type = op["type"]
            if op_type not in operation_totals:
                operation_totals[op_type] = 0.0
            operation_totals[op_type] += op["cost"]
            
        job_data["operation_totals"] = operation_totals
        
        return job_data
    
    def get_budget_report(self) -> Dict:
        """Get a comprehensive budget report."""
        return {
            "total_cost": self.total_cost,
            "budget_cap": self.budget_cap,
            "remaining_budget": self.budget_cap - self.total_cost,
            "budget_utilization_pct": (self.total_cost / self.budget_cap) * 100 if self.budget_cap > 0 else 0,
            "job_count": len(self.jobs),
            "operations_cost": self.operations_cost,
            "operations_pct": {
                op_type: (cost / self.total_cost) * 100 if self.total_cost > 0 else 0
                for op_type, cost in self.operations_cost.items()
            }
        }
    
    def reset(self):
        """Reset all cost tracking."""
        self.total_cost = 0.0
        self.jobs = {}
        self.operations_cost = {
            "scraping": 0.0,
            "tagging": 0.0,
            "embedding": 0.0,
            "analysis": 0.0,
            "other": 0.0
        }
        print("Budget tracker reset")
