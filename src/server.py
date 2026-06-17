import os
import json
import logging
import datetime
import threading
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("impullse-server")

# Clean stale lock file on server startup to prevent Docker container PID 1 reuse locking issues
lock_file = os.path.join("logs", "impullse.lock")
if os.path.exists(lock_file):
    try:
        os.remove(lock_file)
        logger.info("Cleaned stale lock file on server startup.")
    except Exception as e:
        logger.warning(f"Could not clean stale lock file on startup: {str(e)}")

app = FastAPI(
    title="Impullse Analytics Backend",
    description="FastAPI backend exposing endpoints for triggering customer sentiment analysis pipeline and viewing report statuses.",
    version="1.0.0"
)

# Enable CORS for local testing and Vercel routing fallback
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global thread-safe state management
class PipelineState:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = "idle"  # idle, running, failed, completed
        self.last_run_timestamp: Optional[str] = None
        self.last_run_status: Optional[str] = None
        self.error_message: Optional[str] = None

state = PipelineState()

# Pydantic schemas
class RunPayload(BaseModel):
    product: str = Field(default="groww", description="Target product (e.g. groww)")
    start_date: Optional[str] = Field(default=None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(default=None, description="End date in YYYY-MM-DD format")
    dry_run: bool = Field(default=False, description="Run ingestion and analysis without Workspace delivery")
    recipients: Optional[str] = Field(default=None, description="Comma-separated custom recipient emails. Defaults to environment default.")

def get_token_usage() -> int:
    """Helper to read today's token usage from the token log."""
    log_path = "logs/token_usage.json"
    if not os.path.exists(log_path):
        return 0
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
            today_str = datetime.date.today().isoformat()
            return log.get(today_str, 0)
    except Exception:
        return 0

def execute_pipeline_task(payload: RunPayload):
    """Background task executor that calls the CLI callback directly."""
    global state
    
    # 1. Update state to running
    with state.lock:
        state.status = "running"
        state.error_message = None
        
    logger.info(f"Background pipeline execution started for product: {payload.product}")
    
    try:
        from src.cli import run
        
        # Calculate defaults for recipients if not provided
        recipients_val = payload.recipients
        if not recipients_val:
            recipients_val = os.environ.get("STAKEHOLDER_EMAILS", "stakeholders@groww-analytics.internal")
            
        # Execute the Click command callback directly (bypassing Click's CLI arguments context)
        run.callback(
            product=payload.product,
            start_date=payload.start_date,
            end_date=payload.end_date,
            dry_run=payload.dry_run,
            recipients=recipients_val
        )
        
        # Determine status from newly generated logs
        with state.lock:
            state.status = "idle"
            state.last_run_status = "completed_success"
            state.last_run_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
        logger.info("Background pipeline execution completed successfully.")
        
    except Exception as e:
        logger.error(f"Background pipeline execution failed: {str(e)}")
        with state.lock:
            state.status = "failed"
            state.last_run_status = "failed"
            state.error_message = str(e)
            state.last_run_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

@app.get("/")
def read_root():
    return {
        "service": "Impullse Sentiment Analytics Engine API",
        "status": "healthy",
        "documentation": "/docs"
    }

@app.get("/api/status")
def get_status():
    """Returns the current execution status and configuration details."""
    global state
    with state.lock:
        return {
            "status": state.status,
            "last_run_timestamp": state.last_run_timestamp,
            "last_run_status": state.last_run_status,
            "error_message": state.error_message,
            "token_usage_today": get_token_usage(),
            "config": {
                "google_doc_id": os.environ.get("GOOGLE_DOC_ID", "Not Configured"),
                "google_mcp_server_url": os.environ.get("GOOGLE_MCP_SERVER_URL", "Not Configured"),
                "default_recipients": os.environ.get("STAKEHOLDER_EMAILS", "Not Configured")
            }
        }

@app.post("/api/run")
def trigger_run(payload: RunPayload, background_tasks: BackgroundTasks):
    """Triggers the weekly review pulse analysis in a non-blocking background task."""
    global state
    
    with state.lock:
        if state.status == "running":
            raise HTTPException(
                status_code=400,
                detail="A review pulse execution is already in progress. Please wait for it to complete."
            )
            
    # Add to background tasks
    background_tasks.add_task(execute_pipeline_task, payload)
    
    return {
        "status": "accepted",
        "message": f"Sentiment analysis run triggered for {payload.product.upper()} (range: {payload.start_date or 'default'} to {payload.end_date or 'default'}). Check status endpoint for updates.",
        "params": {
            "product": payload.product,
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "dry_run": payload.dry_run
        }
    }

@app.get("/api/reviews")
def get_reviews():
    """Serves the persistent database of normalized & PII-scrubbed reviews."""
    reviews_path = os.path.join("Docs", "reviews.json")
    if not os.path.exists(reviews_path):
        return []
    try:
        with open(reviews_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load reviews database: {str(e)}")

@app.get("/api/runs")
def list_runs():
    """Lists all historical run log audits sorted in reverse chronological order."""
    runs_dir = os.path.join("logs", "runs")
    if not os.path.exists(runs_dir):
        return []
    
    try:
        run_files = [f for f in os.listdir(runs_dir) if f.endswith(".json")]
        runs = []
        for file in run_files:
            file_path = os.path.join(runs_dir, file)
            # Fetch metadata from file header to list quickly without reading entire body
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                runs.append({
                    "run_id": file.replace(".json", ""),
                    "filename": file,
                    "timestamp": data.get("metadata", {}).get("timestamp"),
                    "product": data.get("metadata", {}).get("product"),
                    "iso_week": data.get("metadata", {}).get("iso_week"),
                    "reviews_ingested": data.get("stats", {}).get("reviews_ingested", 0),
                    "total_clusters": data.get("stats", {}).get("total_clusters", 0),
                    "status": data.get("stats", {}).get("status", "unknown")
                })
        # Sort by timestamp descending
        runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list run audits: {str(e)}")

@app.get("/api/runs/{run_id}")
def get_run_details(run_id: str):
    """Retrieves the full structured execution log details for a specific run."""
    run_file = f"{run_id}.json"
    file_path = os.path.join("logs", "runs", run_file)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Run audit log not found: {run_id}")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read run audit log: {str(e)}")
