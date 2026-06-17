import os
import sys

# Add current directory to path to ensure imports work correctly when running from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.cli import run

def main():
    print("==================================================")
    print("Running Impullse Phase 4: Google Workspace Delivery")
    print("==================================================")
    
    product = "groww"
    start_date = os.environ.get("START_DATE", None)
    end_date = os.environ.get("END_DATE", None)
    
    # Read variables from environment
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    mcp_url = os.environ.get("GOOGLE_MCP_SERVER_URL")
    recipients = os.environ.get("STAKEHOLDER_EMAILS", "stakeholders@groww-analytics.internal")
    
    force = os.environ.get("FORCE_DELIVERY", "true").lower() == "true"
    
    print(f"Product: {product.upper()}")
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Google Doc ID: {doc_id}")
    print(f"Google MCP Server URL: {mcp_url}")
    print(f"Recipients: {recipients}")
    print(f"Force Delivery: {force}")
    print("")
    
    if not doc_id:
        print("WARNING: GOOGLE_DOC_ID is not set in environment!")
    if not mcp_url:
        print("WARNING: GOOGLE_MCP_SERVER_URL is not set in environment!")
        
    print("Triggering end-to-end pipeline execution (dry_run=False)...")
    
    try:
        # Trigger the click callback directly
        run.callback(
            product=product,
            start_date=start_date,
            end_date=end_date,
            dry_run=False,
            recipients=recipients,
            force=force
        )
        print("\nPipeline execution completed successfully.")
    except Exception as e:
        print(f"\nPipeline run failed: {str(e)}")

if __name__ == "__main__":
    main()
